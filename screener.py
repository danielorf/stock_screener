from yahoo_finance import Share, YQLQueryError, YQLResponseMalformedError
from datetime import datetime, timedelta
from secutitylist import amex, nasdaq, nyse, the_rest
import pandas as pd
import time
import urllib.error


result_list = []

n_days_ago = 200  # Start stock history returned
date_at_n_days_ago = datetime.now() - timedelta(days=n_days_ago)
sec_list = amex  # Other options: nasdaq, nyse, the_rest

count = 0
for sec in sec_list:
    if '^' not in sec and '.' not in sec:
        print(sec)
        try:
            security = Share(sec.strip())
        except urllib.error.URLError as e1:
            print('Exception! URLError: ', e1)
            continue
        except urllib.error.HTTPError as e2:
            print('Exception! HTTPError: ', e2)
            continue
        except YQLQueryError as e3:
            print('Exception! YQLQueryError: ', e3)
            continue
        except YQLResponseMalformedError as e4:
            print('Exception! YQLResponseMalformedError: ', e4)
            continue
        count += 1
        print(count, 'of', len(sec_list))

        try:
            sec_hist = security.get_historical(str(date_at_n_days_ago.date()), str(datetime.now().date()))
            sec_hist_df = pd.DataFrame(sec_hist)  # Convert stock history dict to pandas dataframe
            sec_hist_df.Close = sec_hist_df.Close.astype(float)  # Ordered by latest first
            close_stdev = sec_hist_df.Close.std()  # Standard deviation of stock over returned time
            price = float(security.get_price())  # Current price
            fifty_day_average = float(security.get_50day_moving_avg())  # 50 day simple moving average
            sec_close_price_array = sec_hist_df.Close.values  # Array of close prices over returned time
            fifteen_day_average = sec_close_price_array[:12].mean()  # 15 day simple moving average
            week_to_week_trend = sec_close_price_array[:6].mean()\
                                 /sec_close_price_array[7:13].mean()-1  # Price trend between the previous week and the
                                                                        # week prior, '>0' indicates improving price
            two_hundred_day_average = float(security.get_200day_moving_avg())  # 200 day simple moving average
            eps_now = float(security.get_EPS_estimate_current_year())  # Earnings per share now
            eps_next_year = float(security.get_EPS_estimate_next_year())  # Earnings per share next year if available
            fifty_two_week_low = float(security.get_year_low())
            fifty_two_week_high = float(security.get_year_high())
            price_earnings_ratio = float(security.get_price_earnings_ratio())

            '''Below is list of conditional checks designed to only return undervalued, but improving stocks'''
            if ((price < (two_hundred_day_average - 2 * close_stdev))  # Below bollinger band minimum @ 200 day, 2 stdev
                and (eps_next_year / eps_now > 1.025)  # Checking for forecasted EPS growth of greater than 10%
                and (fifty_day_average < two_hundred_day_average)  # 50 day MA should be less than 200 day, discounted
                and (fifteen_day_average > fifty_day_average)  # Shows positive recent trend
                and (week_to_week_trend > 0)  # Shows positive recent trend
                and (price_earnings_ratio > 0) and (price_earnings_ratio < 30)  # reasonable p/e range
                and ((fifty_two_week_high - price) / (price - fifty_two_week_low) > 2)):  # Price closer to 52 week low

                result_list.append({'Symbol': sec, 'Price': price, 'SMA15': fifteen_day_average,
                                    'SMA50': fifty_day_average, 'SMA200': two_hundred_day_average, 'EPS': eps_now,
                                    'EPS_NextYearEst': eps_next_year, 'EPS_Ratio': eps_next_year / eps_now,
                                    '52WeekLow': fifty_two_week_low, '52WeekHigh': fifty_two_week_high,
                                    'p_e_ratio': price_earnings_ratio})  # Add passing stocks to the result_list
        except TypeError as e5:
            print('Exception! TypeError: ', e5.args)
            continue
        except urllib.error.URLError as e6:
            print('Exception! URLError: ', e6)
            continue
        except YQLResponseMalformedError as e7:
            print('Exception! YQLResponseMalformedError: ', e7)
            continue
        except AttributeError as e8:
            print('Exception! AttributeError: ', e8)
            continue

    time.sleep(0.05)

print(result_list)
