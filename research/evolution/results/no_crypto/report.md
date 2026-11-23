====================================================================================================
[no_crypto] TEST A: widened search. 43 markets, 9 strategy families, 12 runs per variant, 1,000 bots, 1998 -> 2026-11-23
Pass rule: >= +6.5% in a 5-month period, net of trading costs ($100 version: flat $2 per trade). Holdout = 2018-01 onward.
====================================================================================================

1) THE FROZEN TEN  (fair test: picked in Jan 2018 from older data only, then run untouched; headline run seed 1000, cull 0.1)
   21 five-month windows from 2018-01-01.  Ten-bot portfolio passes in 3 of 21 windows (on $100 with $2 fees: 1).  Mean per 5 months +1.0% (after $2 fees -6.0%); worst -4.7%, best +12.3%; total +20.9%.
   For comparison just holding the S&P 500 passes 8 of 21 (mean +5.4% per 5 months); an equal mix of all markets passes 6 (mean +3.7%).
   #1  [trend    |NIKKEI     |gate:none ] passes  3/21 ($100:  2)  mean +1.2%  worst -8.8%  best +15.8%  holding that market passes 8/21
        Holds NIKKEI while its 10-day average is above its 47-day average (trend following). Position 68% of the account, stop-loss 19%.
   #2  [voltiming|DOW        |gate:none ] passes  2/21 ($100:  2)  mean +1.4%  worst -6.4%  best +12.9%  holding that market passes 5/21
        Holds DOW only while its 58-day volatility is under 20% a year (calm-market timing). Position 68% of the account, stop-loss 5%.
   #3  [reversion|EWY        |gate:news ] passes  2/21 ($100:  0)  mean -1.8%  worst -15.7%  best +12.7%  holding that market passes 9/21
        Buys EWY after it falls 1.5 standard deviations below its 36-day average, sells when it recovers to +1.0 (dip buying); steps aside when today's reading of how much news there is is more than 1.1 std above its norm. Position 82% of the account, stop-loss 9%.
   #4  [breakout |XLI        |gate:none ] passes  6/21 ($100:  4)  mean +3.2%  worst -6.3%  best +22.4%  holding that market passes 7/21
        Buys XLI on a new 5-day high, sells on a new 150-day low (breakout). Position 79% of the account, stop-loss 21%.
   #5  [breakout |XLI        |gate:none ] passes  5/21 ($100:  4)  mean +2.6%  worst -8.0%  best +21.3%  holding that market passes 7/21
        Buys XLI on a new 8-day high, sells on a new 150-day low (breakout). Position 78% of the account, stop-loss 21%.
   #6  [breakout |XLI        |gate:none ] passes  5/21 ($100:  4)  mean +2.6%  worst -8.0%  best +21.3%  holding that market passes 7/21
        Buys XLI on a new 8-day high, sells on a new 150-day low (breakout). Position 78% of the account, stop-loss 21%.
   #7  [regime   |HANGSENG   |gate:macro] passes  1/21 ($100:  0)  mean +0.1%  worst -5.5%  best +12.3%  holding that market passes 7/21
        Holds HANGSENG while above its 249-day average (risk-off timing); steps aside when today's reading of a jump in the VIX is more than 1.2 std above its norm. Position 50% of the account, stop-loss 13%.
   #8  [regime   |HANGSENG   |gate:macro] passes  1/21 ($100:  0)  mean +0.2%  worst -5.5%  best +14.5%  holding that market passes 7/21
        Holds HANGSENG while above its 249-day average (risk-off timing); steps aside when today's reading of a jump in the VIX is more than 1.1 std above its norm. Position 50% of the account, stop-loss 13%.
   #9  [trend    |COPPER     |gate:none ] passes  2/21 ($100:  2)  mean -0.6%  worst -10.9%  best +18.3%  holding that market passes 10/21
        Holds COPPER while its 77-day average is above its 418-day average (trend following). Position 65% of the account, stop-loss 2%.
   #10 [voltiming|XLI        |gate:none ] passes  4/21 ($100:  4)  mean +1.2%  worst -9.8%  best +17.9%  holding that market passes 7/21
        Holds XLI only while its 33-day volatility is under 34% a year (calm-market timing). Position 64% of the account, stop-loss 12%.

   Across all 12 runs, the Frozen Ten portfolio passes 14% of windows (median; range 5% to 29%); mean per 5 months +1.2%; after $2 fees -4.9%.

2) HALL OF FAME  (hindsight list: the bots with the best pass record over their own lives, pooled over 12 runs; expect luck in here)
   #1  [regime   |XLE        |gate:news ] passed 6/6 of its own periods ($100: 4), mean +10.3%; seen in 3 of 12 runs; VERDICT LUCKY?
        Holds XLE all the time (risk-off timing); steps aside when the 5-day average of interest-rate/inflation news is more than 1.3 std below its norm. Position 72% of the account, stop-loss 9%.
        checks: after selection +33% of 49 later periods pass (mean +2.2%); all history +39% vs +52% for holding the market; passes in 17 years
        good: passes spread over 17 different years of history
        warnings: after selection it passes 33% of 49 later periods, mean +2.2% (holding XLE: 47%, mean +4.2%); over all history 39% (mean +2.8%) vs 52% (mean +4.9%) for just holding XLE; makes very few trades per period, so little evidence
   #2  [xsmom    |EWY        |gate:macro] passed 4/4 of its own periods ($100: 2), mean +18.8%; seen in 2 of 12 runs; VERDICT LUCKY?
        Holds EWY while it ranks in the top 43% of all markets by 40-day return (rotation); steps aside when the 20-day average of the VIX fear index is more than 0.9 std above its norm. Position 93% of the account, stop-loss 7%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +30% vs +44% for holding the market; passes in 12 years
        good: passes spread over 12 different years of history
        warnings: only 0 later periods to check; over all history 30% (mean +1.0%) vs 44% (mean +6.5%) for just holding EWY
   #3  [voltiming|KOSPI      |gate:none ] passed 4/4 of its own periods ($100: 1), mean +14.7%; seen in 4 of 12 runs; VERDICT LUCKY?
        Holds KOSPI only while its 28-day volatility is under 33% a year and it is in an uptrend (calm-market timing). Position 84% of the account, stop-loss 9%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +25% vs +41% for holding the market; passes in 13 years
        good: passes spread over 13 different years of history
        warnings: only 0 later periods to check; over all history 25% (mean +1.4%) vs 41% (mean +6.0%) for just holding KOSPI; most passes disappear with $2 fees on $100
   #4  [trend    |KOSPI      |gate:none ] passed 4/4 of its own periods ($100: 1), mean +13.7%; seen in 4 of 12 runs; VERDICT LUCKY?
        Holds KOSPI while its 9-day average is above its 39-day average (trend following). Position 54% of the account, stop-loss 10%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +16% vs +41% for holding the market; passes in 9 years
        good: passes spread over 9 different years of history
        warnings: only 0 later periods to check; over all history 16% (mean +1.8%) vs 41% (mean +6.0%) for just holding KOSPI; most passes disappear with $2 fees on $100
   #5  [trend    |XLV        |gate:none ] passed 4/4 of its own periods ($100: 4), mean +12.5%; seen in 2 of 12 runs; VERDICT LUCKY?
        Holds XLV while its 24-day average is above its 128-day average (trend following). Position 100% of the account, stop-loss 10%.
        checks: after selection +24% of 29 later periods pass (mean +1.1%); all history +23% vs +38% for holding the market; passes in 10 years
        good: passes spread over 10 different years of history
        warnings: after selection it passes 24% of 29 later periods, mean +1.1% (holding XLV: 34%, mean +4.3%); over all history 23% (mean +1.0%) vs 38% (mean +3.8%) for just holding XLV; makes very few trades per period, so little evidence
   #6  [xsmom    |XLK        |gate:none ] passed 4/4 of its own periods ($100: 1), mean +11.4%; seen in 3 of 12 runs; VERDICT LUCKY?
        Holds XLK while it ranks in the top 47% of all markets by 60-day return (rotation). Position 80% of the account, stop-loss 15%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +26% vs +55% for holding the market; passes in 13 years
        good: passes spread over 13 different years of history
        warnings: only 0 later periods to check; over all history 26% (mean +2.4%) vs 55% (mean +5.2%) for just holding XLK; most passes disappear with $2 fees on $100
   #7  [breakout |EWZ        |gate:none ] passed 12/15 of its own periods ($100: 10), mean +9.8%; seen in 7 of 12 runs; VERDICT LUCKY?
        Buys EWZ on a new 8-day high, sells on a new 200-day low (breakout). Position 58% of the account, stop-loss 6%.
        checks: after selection +17% of 41 later periods pass (mean -0.2%); all history +34% vs +50% for holding the market; passes in 14 years
        good: passes spread over 14 different years of history
        warnings: after selection it passes 17% of 41 later periods, mean -0.2% (holding EWZ: 41%, mean +2.3%); over all history 34% (mean +2.1%) vs 50% (mean +6.0%) for just holding EWZ
   #8  [calendar |KOSPI      |gate:none ] passed 6/7 of its own periods ($100: 1), mean +18.6%; seen in 3 of 12 runs; VERDICT LUCKY?
        Holds KOSPI over the last 4 and first 6 trading days of each month (calendar). Position 91% of the account, stop-loss 2%.
        checks: after selection +13% of 62 later periods pass (mean -1.2%); all history +20% vs +41% for holding the market; passes in 10 years
        good: passes spread over 10 different years of history
        warnings: after selection it passes 13% of 62 later periods, mean -1.2% (holding KOSPI: 40%, mean +5.7%); over all history 20% (mean +0.8%) vs 41% (mean +6.0%) for just holding KOSPI; most passes disappear with $2 fees on $100
   #9  [regime   |EWZ        |gate:macro] passed 9/12 of its own periods ($100: 8), mean +9.8%; seen in 6 of 12 runs; VERDICT LUCKY?
        Holds EWZ all the time (risk-off timing); steps aside when the 5-day average of the 60-day move in 10-year yields is more than 1.6 std below its norm. Position 65% of the account, stop-loss 16%.
        checks: after selection +31% of 45 later periods pass (mean +0.8%); all history +40% vs +50% for holding the market; passes in 17 years
        good: passes spread over 17 different years of history
        warnings: after selection it passes 31% of 45 later periods, mean +0.8% (holding EWZ: 42%, mean +2.4%); over all history 40% (mean +2.7%) vs 50% (mean +6.0%) for just holding EWZ; makes very few trades per period, so little evidence
   #10 [trend    |EWZ        |gate:news ] passed 7/9 of its own periods ($100: 6), mean +15.4%; seen in 6 of 12 runs; VERDICT LUCKY?
        Holds EWZ while its 25-day average is above its 66-day average (trend following); steps aside when the 5-day average of interest-rate/inflation news is more than 1.2 std above its norm. Position 95% of the account, stop-loss 10%.
        checks: after selection +22% of 45 later periods pass (mean +0.4%); all history +32% vs +50% for holding the market; passes in 13 years
        good: passes spread over 13 different years of history
        warnings: after selection it passes 22% of 45 later periods, mean +0.4% (holding EWZ: 42%, mean +2.4%); over all history 32% (mean +3.3%) vs 50% (mean +6.0%) for just holding EWZ

3) LUCK BASELINE  (same system, same rules, on FAKE markets where the real returns were shuffled in blocks: no edge exists there)
   Hall of Fame top-10: average share of periods passed    real median 0.77 (runs 0.71..0.82) | fake markets median 0.72 (runs 0.70..0.80)
   Bots passing >= 60% of their periods (count)            real median 74 (runs 21..204) | fake markets median 64 (runs 39..128)
   All bot-periods that pass +6.5% (share)                 real median 0.05 (runs 0.05..0.08) | fake markets median 0.06 (runs 0.05..0.08)
   Frozen Ten portfolio: share of windows passing          real median 0.14 (runs 0.05..0.29) | fake markets median 0.24 (runs 0.05..0.38)
   Frozen Ten portfolio: mean 5-month return               real median +1.2% (runs -0.0%..+2.0%) | fake markets median +2.8% (runs +0.1%..+4.2%)
   Selection skill t-stat, holdout (above +3 = real)       real median +0.3 (runs -0.4..+1.0) | fake markets median +1.2 (runs -0.6..+2.3)

4) DOES NEWS HELP?  (same seeds, three settings)
   news + macro gates           Frozen Ten passes   14% of windows, mean +1.2% per 5m (-4.9% after $2 fees) | Hall-of-Fame top-10 pass rate 77% | all bot-periods passing 5.4% | selection t train +0.7, holdout +0.3
   macro gates only (no news)   Frozen Ten passes   21% of windows, mean +1.3% per 5m (-5.0% after $2 fees) | Hall-of-Fame top-10 pass rate 74% | all bot-periods passing 5.0% | selection t train +0.5, holdout +0.7
   no gates at all              Frozen Ten passes   24% of windows, mean +1.8% per 5m (-3.5% after $2 fees) | Hall-of-Fame top-10 pass rate 77% | all bot-periods passing 5.7% | selection t train +0.6, holdout +0.7
   Gate usage in the main variant: 54% of all bots ever born carry a gate; among Hall-of-Fame bots: 53% (top 30).

5) NEEDS YOUR ATTENTION
   CANDIDATES (kept passing after they were selected, beat just holding the market, spread over 4+ years, survive $2 fees): 0
   WATCH (decent but not proven): 0
   WARNING: 10 of the Hall-of-Fame top 10 look like luck (their record does not hold outside the periods they were picked on).

6) REPEAT OFFENDERS  (family x market combos where ALL bots of that type beat just holding the market, period after period, across every run; 387 combos tested, need t > 3.7)
   pairs     GBPUSD       54 periods  all-bot mean -0.2% vs holding -0.4% -> excess +0.3% per 5m (t=+0.4)  passes 0% of the time vs 11% for holding  
   tsmom     GBPUSD       54 periods  all-bot mean -0.2% vs holding -0.4% -> excess +0.2% per 5m (t=+0.3)  passes 0% of the time vs 11% for holding  
   reversion GBPUSD       54 periods  all-bot mean -0.2% vs holding -0.4% -> excess +0.2% per 5m (t=+0.3)  passes 0% of the time vs 11% for holding  
   xsmom     GBPUSD       54 periods  all-bot mean -0.4% vs holding -0.4% -> excess +0.0% per 5m (t=+0.0)  passes 0% of the time vs 11% for holding  
   trend     GBPUSD       54 periods  all-bot mean -0.6% vs holding -0.4% -> excess -0.1% per 5m (t=-0.2)  passes 0% of the time vs 11% for holding  
   trend     EURUSD       54 periods  all-bot mean -0.1% vs holding +0.0% -> excess -0.1% per 5m (t=-0.2)  passes 0% of the time vs 17% for holding  
   pairs     EURUSD       54 periods  all-bot mean -0.1% vs holding +0.0% -> excess -0.2% per 5m (t=-0.2)  passes 0% of the time vs 17% for holding  
   reversion EURUSD       54 periods  all-bot mean -0.2% vs holding +0.0% -> excess -0.3% per 5m (t=-0.3)  passes 0% of the time vs 17% for holding  
   pairs     AUDUSD       48 periods  all-bot mean -0.2% vs holding +0.2% -> excess -0.4% per 5m (t=-0.4)  passes 0% of the time vs 19% for holding  
   tsmom     EURUSD       54 periods  all-bot mean -0.3% vs holding +0.0% -> excess -0.3% per 5m (t=-0.4)  passes 0% of the time vs 17% for holding  
   Combos clearing the bar: 0 of 387.  (With 387 tries, a few at t>2.5 are expected by luck alone.)

7) WHICH 5-MONTH PERIODS PRODUCE PASSES  (share of ALL bots passing, per period, vs what markets did)
   from 2009-04-01: 24.9% of bots pass | S&P 500 +23.1%  Bitcoin n/a  average bot +4.2%
   from 2005-12-01: 20.4% of bots pass | S&P 500 +3.2%  Bitcoin n/a  average bot +3.1%
   from 2007-03-01: 20.4% of bots pass | S&P 500 +4.5%  Bitcoin n/a  average bot +3.6%
   from 2006-10-02: 17.9% of bots pass | S&P 500 +5.4%  Bitcoin n/a  average bot +2.4%
   from 2010-07-01: 16.1% of bots pass | S&P 500 +17.4%  Bitcoin n/a  average bot +2.4%
   from 2011-10-03: 15.3% of bots pass | S&P 500 +25.0%  Bitcoin n/a  average bot +2.4%
   from 2007-08-01: 13.7% of bots pass | S&P 500 +0.2%  Bitcoin n/a  average bot +0.8%
   from 2005-07-01: 13.0% of bots pass | S&P 500 +5.9%  Bitcoin n/a  average bot +2.0%
   Correlation between 'share of bots passing' and the S&P 500's return in that period: +0.44  (high = passes mostly ride the market)
   Most recent periods: 2024-04-01: 1.2% pass; 2024-09-01: 2.4% pass; 2025-02-01: 4.9% pass; 2025-07-01: 9.5% pass; 2025-12-01: 9.6% pass; 2026-05-01: 5.0% pass

Total time 131s