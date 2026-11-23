====================================================================================================
TEST A: widened search. 44 markets, 9 strategy families, 12 runs per variant, 1,000 bots, 1998 -> 2026-11-23
Pass rule: >= +6.5% in a 5-month period, net of trading costs ($100 version: flat $2 per trade). Holdout = 2018-01 onward.
====================================================================================================

1) THE FROZEN TEN  (fair test: picked in Jan 2018 from older data only, then run untouched; headline run seed 1000, cull 0.1)
   21 five-month windows from 2018-01-01.  Ten-bot portfolio passes in 5 of 21 windows (on $100 with $2 fees: 5).  Mean per 5 months +11.6% (after $2 fees +7.7%); worst -9.5%, best +87.1%; total +471.0%.
   For comparison just holding the S&P 500 passes 8 of 21 (mean +5.4% per 5 months); an equal mix of all markets passes 5 (mean +4.5%).
   #1  [xsmom    |BTC        |gate:macro] passes  6/21 ($100:  5)  mean +12.7%  worst -22.6%  best +149.5%  holding that market passes 8/21
        Holds BTC while it ranks in the top 31% of all markets by 250-day return (rotation); steps aside when the 20-day average of the 60-day move in 10-year yields is more than 2.3 std below its norm. Position 80% of the account, stop-loss 6%.
   #2  [trend    |BTC        |gate:none ] passes  4/21 ($100:  4)  mean +9.1%  worst -12.6%  best +80.0%  holding that market passes 8/21
        Holds BTC while its 33-day average is above its 188-day average (trend following). Position 77% of the account, stop-loss 4%.
   #3  [trend    |BTC        |gate:none ] passes  4/21 ($100:  4)  mean +9.1%  worst -12.6%  best +80.0%  holding that market passes 8/21
        Holds BTC while its 33-day average is above its 188-day average (trend following). Position 77% of the account, stop-loss 4%.
   #4  [trend    |BTC        |gate:none ] passes  4/21 ($100:  4)  mean +9.1%  worst -12.6%  best +80.0%  holding that market passes 8/21
        Holds BTC while its 33-day average is above its 188-day average (trend following). Position 77% of the account, stop-loss 4%.
   #5  [tsmom    |BTC        |gate:none ] passes  6/21 ($100:  6)  mean +14.0%  worst -13.6%  best +129.1%  holding that market passes 8/21
        Holds BTC while its 234-day return is above 0.6% (momentum). Position 72% of the account, stop-loss 6%.
   #6  [tsmom    |BTC        |gate:none ] passes  6/21 ($100:  5)  mean +13.7%  worst -12.5%  best +126.3%  holding that market passes 8/21
        Holds BTC while its 183-day return is above -0.5% (momentum). Position 71% of the account, stop-loss 5%.
   #7  [tsmom    |BTC        |gate:none ] passes  6/21 ($100:  5)  mean +13.6%  worst -12.5%  best +126.3%  holding that market passes 8/21
        Holds BTC while its 183-day return is above -0.5% (momentum). Position 71% of the account, stop-loss 6%.
   #8  [breakout |BTC        |gate:macro] passes  5/21 ($100:  5)  mean +12.3%  worst -12.5%  best +130.8%  holding that market passes 8/21
        Buys BTC on a new 100-day high, sells on a new 60-day low (breakout); steps aside when the 20-day average of the VIX fear index is more than 1.0 std above its norm. Position 72% of the account, stop-loss 5%.
   #9  [breakout |BTC        |gate:news ] passes  7/21 ($100:  7)  mean +13.8%  worst -17.4%  best +114.4%  holding that market passes 8/21
        Buys BTC on a new 60-day high, sells on a new 80-day low (breakout); steps aside when the 20-day average of interest-rate/inflation news is more than 1.2 std above its norm. Position 65% of the account, stop-loss 8%.
   #10 [xsmom    |BTC        |gate:macro] passes  6/21 ($100:  5)  mean +8.4%  worst -16.9%  best +106.7%  holding that market passes 8/21
        Holds BTC while it ranks in the top 25% of all markets by 250-day return (rotation); steps aside when the 20-day average of the 60-day move in 10-year yields is more than 1.9 std below its norm. Position 62% of the account, stop-loss 8%.

   Across all 12 runs, the Frozen Ten portfolio passes 29% of windows (median; range 24% to 38%); mean per 5 months +11.1%; after $2 fees +3.6%.

2) HALL OF FAME  (hindsight list: the bots with the best pass record over their own lives, pooled over 12 runs; expect luck in here)
   #1  [trend    |KOSPI      |gate:news ] passed 4/4 of its own periods ($100: 2), mean +18.0%; seen in 4 of 12 runs; VERDICT LUCKY?
        Holds KOSPI while its 19-day average is above its 78-day average (trend following); steps aside when today's reading of oil/energy news is more than 1.2 std below its norm. Position 71% of the account, stop-loss 4%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +25% vs +41% for holding the market; passes in 13 years
        good: passes spread over 13 different years of history
        warnings: only 0 later periods to check; over all history 25% (mean +2.5%) vs 41% (mean +6.0%) for just holding KOSPI
   #2  [breakout |KOSPI      |gate:none ] passed 4/4 of its own periods ($100: 3), mean +15.7%; seen in 2 of 12 runs; VERDICT LUCKY?
        Buys KOSPI on a new 100-day high, sells on a new 20-day low (breakout). Position 79% of the account, stop-loss 8%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +19% vs +41% for holding the market; passes in 10 years
        good: passes spread over 10 different years of history
        warnings: only 0 later periods to check; over all history 19% (mean +1.8%) vs 41% (mean +6.0%) for just holding KOSPI
   #3  [voltiming|KOSPI      |gate:none ] passed 4/4 of its own periods ($100: 1), mean +13.9%; seen in 3 of 12 runs; VERDICT LUCKY?
        Holds KOSPI only while its 21-day volatility is under 35% a year and it is in an uptrend (calm-market timing). Position 87% of the account, stop-loss 12%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +25% vs +41% for holding the market; passes in 13 years
        good: passes spread over 13 different years of history
        warnings: only 0 later periods to check; over all history 25% (mean +1.3%) vs 41% (mean +6.0%) for just holding KOSPI; most passes disappear with $2 fees on $100
   #4  [calendar |KOSPI      |gate:none ] passed 6/7 of its own periods ($100: 1), mean +18.6%; seen in 2 of 12 runs; VERDICT LUCKY?
        Holds KOSPI over the last 4 and first 6 trading days of each month (calendar). Position 91% of the account, stop-loss 2%.
        checks: after selection +13% of 62 later periods pass (mean -1.2%); all history +20% vs +41% for holding the market; passes in 10 years
        good: passes spread over 10 different years of history
        warnings: after selection it passes 13% of 62 later periods, mean -1.2% (holding KOSPI: 40%, mean +5.7%); over all history 20% (mean +0.8%) vs 41% (mean +6.0%) for just holding KOSPI; most passes disappear with $2 fees on $100
   #5  [regime   |GOLD       |gate:news ] passed 6/7 of its own periods ($100: 5), mean +11.1%; seen in 4 of 12 runs; VERDICT LUCKY?
        Holds GOLD all the time (risk-off timing); steps aside when the 20-day average of interest-rate/inflation news is more than 0.7 std above its norm. Position 94% of the account, stop-loss 23%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +37% vs +39% for holding the market; passes in 16 years
        good: passes spread over 16 different years of history
        warnings: only 0 later periods to check; over all history 37% (mean +4.2%) vs 39% (mean +5.0%) for just holding GOLD; makes very few trades per period, so little evidence
   #6  [tsmom    |XLE        |gate:news ] passed 6/7 of its own periods ($100: 4), mean +7.8%; seen in 1 of 12 runs; VERDICT LUCKY?
        Holds XLE while its 111-day return is above 1.0% (momentum); steps aside when the 20-day average of health/pandemic news is more than 2.5 std above its norm. Position 82% of the account, stop-loss 14%.
        checks: after selection +21% of 48 later periods pass (mean +1.3%); all history +24% vs +52% for holding the market; passes in 12 years
        good: passes spread over 12 different years of history
        warnings: after selection it passes 21% of 48 later periods, mean +1.3% (holding XLE: 48%, mean +4.5%); over all history 24% (mean +1.3%) vs 52% (mean +4.9%) for just holding XLE
   #7  [breakout |EWZ        |gate:news ] passed 10/13 of its own periods ($100: 8), mean +10.4%; seen in 9 of 12 runs; VERDICT LUCKY?
        Buys EWZ on a new 13-day high, sells on a new 150-day low (breakout); steps aside when the 5-day average of oil/energy news is more than 2.2 std below its norm. Position 71% of the account, stop-loss 7%.
        checks: after selection +21% of 42 later periods pass (mean +1.3%); all history +35% vs +50% for holding the market; passes in 15 years
        good: passes spread over 15 different years of history
        warnings: after selection it passes 21% of 42 later periods, mean +1.3% (holding EWZ: 43%, mean +3.3%); over all history 35% (mean +3.2%) vs 50% (mean +6.0%) for just holding EWZ
   #8  [pairs    |XLK        |gate:news ] passed 5/6 of its own periods ($100: 1), mean +9.5%; seen in 1 of 12 runs; VERDICT LUCKY?
        Buys XLK when it lags LQD by 0.5 standard deviations over 20 days, sells when the gap closes to +0.8 (relative value); steps aside when the 20-day average of tariff/sanctions news is more than 1.7 std above its norm. Position 100% of the account, stop-loss 25%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +27% vs +55% for holding the market; passes in 13 years
        good: passes spread over 13 different years of history
        warnings: only 0 later periods to check; over all history 27% (mean +2.1%) vs 55% (mean +5.2%) for just holding XLK; most passes disappear with $2 fees on $100
   #9  [regime   |XLV        |gate:news ] passed 5/6 of its own periods ($100: 2), mean +5.6%; seen in 2 of 12 runs; VERDICT LUCKY?
        Holds XLV all the time (risk-off timing); steps aside when today's reading of tariff/sanctions news is more than 1.9 std below its norm. Position 91% of the account, stop-loss 6%.
        checks: after selection +23% of 26 later periods pass (mean +0.6%); all history +30% vs +38% for holding the market; passes in 14 years
        good: passes spread over 14 different years of history
        warnings: after selection it passes 23% of 26 later periods, mean +0.6% (holding XLV: 31%, mean +4.2%); over all history 30% (mean +1.5%) vs 38% (mean +3.8%) for just holding XLV; makes very few trades per period, so little evidence; most passes disappear with $2 fees on $100
   #10 [voltiming|EWZ        |gate:none ] passed 8/11 of its own periods ($100: 7), mean +7.0%; seen in 2 of 12 runs; VERDICT LUCKY?
        Holds EWZ only while its 42-day volatility is under 39% a year (calm-market timing). Position 47% of the account, stop-loss 22%.
        checks: after selection +16% of 45 later periods pass (mean -0.5%); all history +26% vs +50% for holding the market; passes in 10 years
        good: passes spread over 10 different years of history
        warnings: after selection it passes 16% of 45 later periods, mean -0.5% (holding EWZ: 42%, mean +2.4%); over all history 26% (mean +0.7%) vs 50% (mean +6.0%) for just holding EWZ; makes very few trades per period, so little evidence

3) LUCK BASELINE  (same system, same rules, on FAKE markets where the real returns were shuffled in blocks: no edge exists there)
   Hall of Fame top-10: average share of periods passed    real median 0.77 (runs 0.71..0.82) | fake markets median 0.73 (runs 0.67..0.82)
   Bots passing >= 60% of their periods (count)            real median 74 (runs 41..258) | fake markets median 66 (runs 43..139)
   All bot-periods that pass +6.5% (share)                 real median 0.07 (runs 0.06..0.10) | fake markets median 0.06 (runs 0.04..0.08)
   Frozen Ten portfolio: share of windows passing          real median 0.29 (runs 0.24..0.38) | fake markets median 0.29 (runs 0.14..0.52)
   Frozen Ten portfolio: mean 5-month return               real median +11.1% (runs +5.0%..+12.8%) | fake markets median +2.9% (runs +0.2%..+6.1%)
   Selection skill t-stat, holdout (above +3 = real)       real median +1.1 (runs +0.5..+1.7) | fake markets median +2.1 (runs +0.2..+2.8)

4) DOES NEWS HELP?  (same seeds, three settings)
   news + macro gates           Frozen Ten passes   29% of windows, mean +11.1% per 5m (+3.6% after $2 fees) | Hall-of-Fame top-10 pass rate 77% | all bot-periods passing 7.0% | selection t train +1.4, holdout +1.1
   macro gates only (no news)   Frozen Ten passes   29% of windows, mean +8.9% per 5m (+2.1% after $2 fees) | Hall-of-Fame top-10 pass rate 76% | all bot-periods passing 6.5% | selection t train +1.6, holdout +1.2
   no gates at all              Frozen Ten passes   29% of windows, mean +10.3% per 5m (+3.5% after $2 fees) | Hall-of-Fame top-10 pass rate 76% | all bot-periods passing 7.1% | selection t train +1.7, holdout +1.1
   Gate usage in the main variant: 53% of all bots ever born carry a gate; among Hall-of-Fame bots: 67% (top 30).

5) NEEDS YOUR ATTENTION
   CANDIDATES (kept passing after they were selected, beat just holding the market, spread over 4+ years, survive $2 fees): 0
   WATCH (decent but not proven): 0
   WARNING: 10 of the Hall-of-Fame top 10 look like luck (their record does not hold outside the periods they were picked on).

6) REPEAT OFFENDERS  (family x market combos where ALL bots of that type beat just holding the market, period after period, across every run; 396 combos tested, need t > 3.7)
   reversion GBPUSD       54 periods  all-bot mean -0.1% vs holding -0.4% -> excess +0.3% per 5m (t=+0.4)  passes 0% of the time vs 11% for holding  
   pairs     GBPUSD       54 periods  all-bot mean -0.3% vs holding -0.4% -> excess +0.1% per 5m (t=+0.2)  passes 0% of the time vs 11% for holding  
   tsmom     GBPUSD       54 periods  all-bot mean -0.4% vs holding -0.4% -> excess -0.0% per 5m (t=-0.0)  passes 0% of the time vs 11% for holding  
   reversion EURUSD       54 periods  all-bot mean -0.2% vs holding +0.0% -> excess -0.2% per 5m (t=-0.2)  passes 0% of the time vs 17% for holding  
   breakout  GBPUSD       54 periods  all-bot mean -0.6% vs holding -0.4% -> excess -0.2% per 5m (t=-0.3)  passes 1% of the time vs 11% for holding  
   trend     GBPUSD       54 periods  all-bot mean -0.6% vs holding -0.4% -> excess -0.2% per 5m (t=-0.3)  passes 0% of the time vs 11% for holding  
   trend     EURUSD       53 periods  all-bot mean -0.4% vs holding -0.2% -> excess -0.2% per 5m (t=-0.3)  passes 1% of the time vs 15% for holding  
   breakout  EURUSD       54 periods  all-bot mean -0.2% vs holding +0.0% -> excess -0.2% per 5m (t=-0.3)  passes 0% of the time vs 17% for holding  
   xsmom     GBPUSD       54 periods  all-bot mean -0.7% vs holding -0.4% -> excess -0.2% per 5m (t=-0.3)  passes 0% of the time vs 11% for holding  
   pairs     AUDUSD       48 periods  all-bot mean -0.2% vs holding +0.2% -> excess -0.4% per 5m (t=-0.3)  passes 0% of the time vs 19% for holding  
   Combos clearing the bar: 0 of 396.  (With 396 tries, a few at t>2.5 are expected by luck alone.)

7) WHICH 5-MONTH PERIODS PRODUCE PASSES  (share of ALL bots passing, per period, vs what markets did)
   from 2020-07-01: 29.4% of bots pass | S&P 500 +17.5%  Bitcoin +103.8%  average bot +11.3%
   from 2023-11-01: 27.5% of bots pass | S&P 500 +23.7%  Bitcoin +96.7%  average bot +11.8%
   from 2020-12-01: 26.7% of bots pass | S&P 500 +14.2%  Bitcoin +207.5%  average bot +23.3%
   from 2024-09-01: 24.6% of bots pass | S&P 500 +6.9%  Bitcoin +75.6%  average bot +7.5%
   from 2005-12-01: 22.0% of bots pass | S&P 500 +3.2%  Bitcoin n/a  average bot +3.6%
   from 2019-04-01: 21.8% of bots pass | S&P 500 +2.1%  Bitcoin +134.7%  average bot +8.0%
   from 2007-03-01: 21.5% of bots pass | S&P 500 +4.5%  Bitcoin n/a  average bot +3.6%
   from 2009-04-01: 19.6% of bots pass | S&P 500 +23.1%  Bitcoin n/a  average bot +3.3%
   Correlation between 'share of bots passing' and the S&P 500's return in that period: +0.50  (high = passes mostly ride the market)
   Most recent periods: 2024-04-01: 2.9% pass; 2024-09-01: 24.6% pass; 2025-02-01: 6.0% pass; 2025-07-01: 5.7% pass; 2025-12-01: 8.1% pass; 2026-05-01: 7.9% pass

Total time 100s