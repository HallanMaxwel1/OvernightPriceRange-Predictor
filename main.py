import pandas as pd
from datetime import datetime, timedelta

#This operates under the normal U.S calendar
def get_previous_trading_day(date_obj):
    """Get the previous trading day (skipping weekends only)"""
    prev_day = date_obj - timedelta(days=1)

    # Keep going back until we find a weekday
    while prev_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
        prev_day = prev_day - timedelta(days=1)

    return prev_day


def filter_by_date(headlines_2021, headlines_2022, headlines_2023, headlines_2024, prices_path, target_date):
    """
    Filter rows by a specific date from headline files.
    Also calculates 20-day rolling statistics for symbols.
    Includes after-market data (after 4:31 PM) from the previous trading day.

    Args:
        headlines_2021: Path to 2021 headlines TSV
        headlines_2022: Path to 2022 headlines TSV
        headlines_2023: Path to 2023 headlines TSV
        headlines_2024: Path to 2024 headlines TSV
        prices_path: Path to the prices TSV file
        target_date: User-input Date string in format 'M/D/YYYY' (e.g., '5/6/2024')

    Returns:
        Filtered DataFrame with headlines and statistics
    """
    # Parse the target date
    target_date_obj = datetime.strptime(target_date, '%m/%d/%Y').date()

    # Get the previous trading day
    previous_trading_day = get_previous_trading_day(target_date_obj)

    # Create cutoff times
    # Previous trading day: after 4:31 PM (16:31)
    start_cutoff = datetime.combine(previous_trading_day, datetime.strptime('16:31', '%H:%M').time())
    # Target day: up to and including 9:30 AM (market open)
    end_cutoff = datetime.combine(target_date_obj, datetime.strptime('09:30', '%H:%M').time()) + timedelta(seconds=59)

    print(f"Target date: {target_date_obj.strftime('%A, %m/%d/%Y')}")
    print(f"Previous trading day: {previous_trading_day.strftime('%A, %m/%d/%Y')}")
    print(f"Time window: {start_cutoff.strftime('%m/%d/%Y %I:%M %p')} to {end_cutoff.strftime('%m/%d/%Y %I:%M %p')}")
    print()

    # Filter criteria function
    def matches_criteria(timestamp):
        if pd.isna(timestamp):
            return False

        dt = None
        if isinstance(timestamp, datetime):
            dt = timestamp
        else:
            try:
                dt = pd.to_datetime(timestamp)
            except:
                return False

        # Include only timestamps between:
        # 4:31 PM on previous trading day and 9:30:59 AM on target date
        if dt >= start_cutoff and dt <= end_cutoff:
            return True

        return False

    # Load all 4 headline files
    df_2021 = pd.read_csv(headlines_2021, sep='\t')
    df_2022 = pd.read_csv(headlines_2022, sep='\t')
    df_2023 = pd.read_csv(headlines_2023, sep='\t')
    df_2024 = pd.read_csv(headlines_2024, sep='\t')

    # Combine all headline dataframes
    df_headlines = pd.concat([df_2021, df_2022, df_2023, df_2024], ignore_index=True)

    # Find the timestamp column
    timestamp_col = None
    for col in df_headlines.columns:
        if 'time' in col.lower() or 'date' in col.lower():
            timestamp_col = col
            break

    if timestamp_col is None:
        timestamp_col = df_headlines.columns[0]

    # Convert timestamp column to datetime
    df_headlines[timestamp_col] = pd.to_datetime(df_headlines[timestamp_col])

    # Filter headlines based on time window
    filtered_headlines = df_headlines[df_headlines[timestamp_col].apply(matches_criteria)].copy()

    # Process price data and calculate 20-day rolling statistics
    df_prices = pd.read_csv(prices_path, sep='\t')
    df_prices['date'] = pd.to_datetime(df_prices['date'])

    # Calculate 20-day rolling statistics for each symbol
    rolling_stats_dict = {}

    # Find symbol column name
    symbol_col = None
    for col in df_prices.columns:
        if 'symbol' in col.lower() or 'ticker' in col.lower():
            symbol_col = col
            break

    if symbol_col is None:
        symbol_col = df_prices.columns[1]  # Default to second column if not found

    for symbol in df_prices[symbol_col].unique():
        symbol_data = df_prices[df_prices[symbol_col] == symbol].sort_values('date')

        # Find the target date in the data
        target_row = symbol_data[symbol_data['date'].dt.date == target_date_obj]

        if not target_row.empty:
            # Get the 20 days prior to (but not including) the target date
            prior_data = symbol_data[symbol_data['date'] < target_row['date'].iloc[0]].tail(20)

            if len(prior_data) >= 20:
                rolling_std = prior_data['close'].std()
                rolling_avg = prior_data['close'].mean()
                rolling_std_pct = (rolling_std / rolling_avg) * 100 if rolling_avg != 0 else None

                # Get yesterday's closing price (most recent day in the 20-day window)
                yesterday_close = prior_data.iloc[-1]['close']

                # Calculate bounds: avg +/- (std% of yesterday's close)
                std_dollar_amount = (rolling_std_pct / 100) * yesterday_close if rolling_std_pct is not None else None
                upper_bound = rolling_avg + std_dollar_amount if std_dollar_amount is not None else None
                lower_bound = rolling_avg - std_dollar_amount if std_dollar_amount is not None else None
                price_range = upper_bound - lower_bound if (
                            upper_bound is not None and lower_bound is not None) else None

                rolling_stats_dict[symbol] = {
                    'stdevOfClose': rolling_std,
                    'Closeavg': rolling_avg,
                    'stdev_pctOfClose': rolling_std_pct,
                    'prevClose': yesterday_close,
                    'Closeavg_plus_stdevpct': upper_bound,
                    'Closeavg_minus_stdevpct': lower_bound,
                    'price_range': price_range
                }

    # Merge headlines with rolling statistics
    if not filtered_headlines.empty and rolling_stats_dict:
        # Find symbol column in headlines
        headline_symbol_col = None
        for col in filtered_headlines.columns:
            if 'symbol' in col.lower() or 'ticker' in col.lower():
                headline_symbol_col = col
                break

        if headline_symbol_col:
            # Print all statistical columns based on symbol
            filtered_headlines['prevClose'] = filtered_headlines[headline_symbol_col].map(
                lambda s: rolling_stats_dict.get(s, {}).get('prevClose'))
            filtered_headlines['20d_stdevOfClose'] = filtered_headlines[headline_symbol_col].map(
                lambda s: rolling_stats_dict.get(s, {}).get('stdevOfClose'))
            filtered_headlines['20d_Closeavg'] = filtered_headlines[headline_symbol_col].map(
                lambda s: rolling_stats_dict.get(s, {}).get('Closeavg'))
            filtered_headlines['20d_stdev_pctOfClose'] = filtered_headlines[headline_symbol_col].map(
                lambda s: rolling_stats_dict.get(s, {}).get('stdev_pctOfClose'))
            filtered_headlines['20d_Closeavg_plus_stdevpct'] = filtered_headlines[headline_symbol_col].map(
                lambda s: rolling_stats_dict.get(s, {}).get('Closeavg_plus_stdevpct'))
            filtered_headlines['20d_Closeavg_minus_stdevpct'] = filtered_headlines[headline_symbol_col].map(
                lambda s: rolling_stats_dict.get(s, {}).get('Closeavg_minus_stdevpct'))
            filtered_headlines['stdev_price_range'] = filtered_headlines[headline_symbol_col].map(
                lambda s: rolling_stats_dict.get(s, {}).get('price_range'))

            # Reorder columns for better readability
            base_cols = [timestamp_col, headline_symbol_col, 'prevClose', '20d_stdevOfClose', '20d_Closeavg',
                         '20d_stdev_pctOfClose', '20d_Closeavg_plus_stdevpct', '20d_Closeavg_minus_stdevpct',
                         'stdev_price_range']
            other_cols = [c for c in filtered_headlines.columns if c not in base_cols]
            cols = base_cols + other_cols
            # Only include columns that exist
            cols = [c for c in cols if c in filtered_headlines.columns]
            filtered_headlines = filtered_headlines[cols]

    return filtered_headlines


# Example usage (Testing)
if __name__ == "__main__":
    # Prompt user for date
    target_date = input("Enter date to filter (format M/D/YYYY, e.g., 5/6/2024): ")

# Goes through each year's file to find the right headline
    try:
        result = filter_by_date(
            "temp_offerings_2021_anon.tsv",
            "temp_offerings_2022_anon.tsv",
            "temp_offerings_2023_anon.tsv",
            "temp_offerings_2024_anon.tsv",
            "temp_prices_2021_2024_anon.tsv",
            target_date
        )

        print("=" * 80)
        print(f"HEADLINES WITH ROLLING STATISTICS: {len(result)} rows")
        print("=" * 80)
        if not result.empty:
            print(result.to_string(index=False))
        else:
            print("No matching rows found.")

        # Optional: Save to file
        save = input("\nSave results to file? (y/n): ")
        if save.lower() == 'y':
            output_file = f"filtered_headlines_{target_date.replace('/', '-')}.csv"
            result.to_csv(output_file, index=False)
            print(f"Saved results to {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()