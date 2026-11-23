====================================================================================================
[diversified] TEST A: widened search. 45 markets, 9 strategy families, 12 runs per variant, 1,000 bots, 1998 -> 2026-11-23
Pass rule: >= +6.5% in a 5-month period, net of trading costs ($100 version: flat $2 per trade). Holdout = 2018-01 onward.
====================================================================================================

1) THE FROZEN TEN  (fair test: picked in Jan 2018 from older data only, then run untouched; headline run seed 1000, cull 0.1)
   21 five-month windows from 2018-01-01.  Ten-bot portfolio passes in 6 of 21 windows (on $100 with $2 fees: 3).  Mean per 5 months +3.8% (after $2 fees -3.8%); worst -8.1%, best +44.0%; total +84.8%.
   For comparison just holding the S&P 500 passes 8 of 21 (mean +5.4% per 5 months); an equal mix of all markets passes 5 (mean +4.6%).
   #1  [trend    |BTC        |gate:none ] passes  6/21 ($100:  6)  mean +16.3%  worst -13.6%  best +155.9%  holding that market passes 8/21
        Holds BTC while its 115-day average is above its 533-day average (trend following). Position 82% of the account, stop-loss 7%.
   #2  [trend    |BTC        |gate:macro] passes  7/21 ($100:  7)  mean +11.2%  worst -21.9%  best +110.3%  holding that market passes 8/21
        Holds BTC while its 109-day average is above its 435-day average (trend following); steps aside when the 20-day average of the yield-curve slope (10yr minus 3-month) is more than 2.3 std above its norm. Position 82% of the account, stop-loss 19%.
   #3  [regime   |ETH        |gate:macro] passes  4/21 ($100:  4)  mean +4.3%  worst -26.5%  best +104.2%  holding that market passes 11/21
        Holds ETH all the time (risk-off timing); steps aside when today's reading of the yield-curve slope (10yr minus 3-month) is more than 2.5 std below its norm. Position 71% of the account, stop-loss 4%.
   #4  [regime   |ETH        |gate:macro] passes  4/21 ($100:  4)  mean +4.3%  worst -26.5%  best +104.2%  holding that market passes 11/21
        Holds ETH all the time (risk-off timing); steps aside when today's reading of the yield-curve slope (10yr minus 3-month) is more than 2.5 std below its norm. Position 71% of the account, stop-loss 4%.
   #5  [voltiming|EWW        |gate:none ] passes  5/21 ($100:  0)  mean -1.0%  worst -16.5%  best +19.2%  holding that market passes 10/21
        Holds EWW only while its 29-day volatility is under 38% a year and it is in an uptrend (calm-market timing). Position 100% of the account, stop-loss 18%.
   #6  [voltiming|NASDAQ     |gate:none ] passes  9/21 ($100:  7)  mean +4.0%  worst -16.2%  best +24.1%  holding that market passes 12/21
        Holds NASDAQ only while its 56-day volatility is under 33% a year (calm-market timing). Position 96% of the account, stop-loss 19%.
   #7  [calendar |NATGAS     |gate:none ] passes  5/21 ($100:  1)  mean -0.3%  worst -46.1%  best +54.9%  holding that market passes 10/21
        Holds NATGAS over the last 5 and first 0 trading days of each month (calendar). Position 85% of the account, stop-loss 3%.
   #8  [breakout |OIL        |gate:macro] passes  3/21 ($100:  2)  mean +1.4%  worst -8.3%  best +30.9%  holding that market passes 7/21
        Buys OIL on a new 150-day high, sells on a new 150-day low (breakout); steps aside when the 5-day average of the VIX fear index is more than 2.4 std above its norm. Position 54% of the account, stop-loss 7%.
   #9  [calendar |USDJPY     |gate:none ] passes  0/21 ($100:  0)  mean -2.1%  worst -7.7%  best +0.3%  holding that market passes 3/21
        Holds USDJPY over the last 3 and first 3 trading days of each month (calendar). Position 63% of the account, stop-loss 3%.
   #10 [regime   |HANGSENG   |gate:news ] passes  4/21 ($100:  3)  mean -0.3%  worst -7.3%  best +14.8%  holding that market passes 7/21
        Holds HANGSENG all the time (risk-off timing); steps aside when today's reading of financial-crisis news is more than 1.6 std below its norm. Position 78% of the account, stop-loss 7%.

   Across all 12 runs, the Frozen Ten portfolio passes 24% of windows (median; range 10% to 33%); mean per 5 months +3.8%; after $2 fees -3.1%.

2) HALL OF FAME  (hindsight list: the bots with the best pass record over their own lives, pooled over 12 runs; expect luck in here)
   #1  [breakout |EWZ        |gate:news ] passed 8/9 of its own periods ($100: 8), mean +17.3%; seen in 5 of 12 runs; VERDICT LUCKY?
        Buys EWZ on a new 5-day high, sells on a new 200-day low (breakout); steps aside when the 5-day average of financial-crisis news is more than 2.2 std below its norm. Position 82% of the account, stop-loss 5%.
        checks: after selection +30% of 44 later periods pass (mean -0.7%); all history +44% vs +50% for holding the market; passes in 18 years
        good: passes spread over 18 different years of history
        warnings: after selection it passes 30% of 44 later periods, mean -0.7% (holding EWZ: 41%, mean +1.9%); over all history 44% (mean +2.8%) vs 50% (mean +6.0%) for just holding EWZ
   #2  [voltiming|KOSPI      |gate:macro] passed 4/4 of its own periods ($100: 3), mean +24.7%; seen in 2 of 12 runs; VERDICT LUCKY?
        Holds KOSPI only while its 43-day volatility is under 37% a year (calm-market timing); steps aside when the 5-day average of the yield-curve slope (10yr minus 3-month) is more than 0.8 std below its norm. Position 100% of the account, stop-loss 13%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +20% vs +41% for holding the market; passes in 10 years
        good: passes spread over 10 different years of history
        warnings: only 0 later periods to check; over all history 20% (mean +1.2%) vs 41% (mean +6.0%) for just holding KOSPI
   #3  [trend    |EWY        |gate:none ] passed 4/4 of its own periods ($100: 1), mean +11.5%; seen in 1 of 12 runs; VERDICT LUCKY?
        Holds EWY while its 12-day average is above its 70-day average (trend following). Position 41% of the account, stop-loss 3%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +17% vs +44% for holding the market; passes in 9 years
        good: passes spread over 9 different years of history
        warnings: only 0 later periods to check; over all history 17% (mean +1.5%) vs 44% (mean +6.5%) for just holding EWY; most passes disappear with $2 fees on $100
   #4  [breakout |EWW        |gate:none ] passed 4/4 of its own periods ($100: 2), mean +11.2%; seen in 3 of 12 runs; VERDICT LUCKY?
        Buys EWW on a new 10-day high, sells on a new 250-day low (breakout). Position 90% of the account, stop-loss 8%.
        checks: after selection +37% of 46 later periods pass (mean +1.0%); all history +41% vs +45% for holding the market; passes in 20 years
        good: passes spread over 20 different years of history
        warnings: after selection it passes 37% of 46 later periods, mean +1.0% (holding EWW: 41%, mean +2.8%); over all history 41% (mean +1.9%) vs 45% (mean +4.6%) for just holding EWW; makes very few trades per period, so little evidence
   #5  [trend    |EWZ        |gate:none ] passed 8/10 of its own periods ($100: 8), mean +15.7%; seen in 5 of 12 runs; VERDICT LUCKY?
        Holds EWZ while its 23-day average is above its 49-day average (trend following). Position 92% of the account, stop-loss 7%.
        checks: after selection +17% of 47 later periods pass (mean +0.6%); all history +27% vs +50% for holding the market; passes in 12 years
        good: passes spread over 12 different years of history
        warnings: after selection it passes 17% of 47 later periods, mean +0.6% (holding EWZ: 45%, mean +3.7%); over all history 27% (mean +3.2%) vs 50% (mean +6.0%) for just holding EWZ
   #6  [regime   |EWZ        |gate:news ] passed 7/9 of its own periods ($100: 6), mean +11.9%; seen in 3 of 12 runs; VERDICT LUCKY?
        Holds EWZ while above its 179-day average (risk-off timing); steps aside when the 20-day average of health/pandemic news is more than 2.1 std below its norm. Position 84% of the account, stop-loss 23%.
        checks: after selection +25% of 48 later periods pass (mean +0.6%); all history +31% vs +50% for holding the market; passes in 12 years
        good: passes spread over 12 different years of history
        warnings: after selection it passes 25% of 48 later periods, mean +0.6% (holding EWZ: 46%, mean +4.0%); over all history 31% (mean +2.0%) vs 50% (mean +6.0%) for just holding EWZ
   #7  [voltiming|XLY        |gate:none ] passed 7/9 of its own periods ($100: 3), mean +8.0%; seen in 2 of 12 runs; VERDICT LUCKY?
        Holds XLY only while its 22-day volatility is under 27% a year (calm-market timing). Position 73% of the account, stop-loss 7%.
        checks: after selection +19% of 31 later periods pass (mean +1.7%); all history +27% vs +39% for holding the market; passes in 13 years
        good: passes spread over 13 different years of history
        warnings: after selection it passes 19% of 31 later periods, mean +1.7% (holding XLY: 35%, mean +4.9%); over all history 27% (mean +1.4%) vs 39% (mean +4.3%) for just holding XLY; most passes disappear with $2 fees on $100
   #8  [voltiming|GOLD       |gate:none ] passed 5/6 of its own periods ($100: 4), mean +8.8%; seen in 1 of 12 runs; VERDICT LUCKY?
        Holds GOLD only while its 39-day volatility is under 40% a year (calm-market timing). Position 77% of the account, stop-loss 5%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +29% vs +39% for holding the market; passes in 13 years
        good: passes spread over 13 different years of history
        warnings: only 0 later periods to check; over all history 29% (mean +1.8%) vs 39% (mean +5.0%) for just holding GOLD; makes very few trades per period, so little evidence
   #9  [breakout |ETH        |gate:macro] passed 6/8 of its own periods ($100: 2), mean +14.5%; seen in 3 of 12 runs; VERDICT LUCKY?
        Buys ETH on a new 13-day high, sells on a new 13-day low (breakout); steps aside when the 5-day average of the 60-day move in 10-year yields is more than 1.5 std below its norm. Position 46% of the account, stop-loss 3%.
        checks: after selection +25% of 8 later periods pass (mean +1.3%); all history +52% vs +52% for holding the market; passes in 7 years
        good: passes spread over 7 different years of history
        warnings: after selection it passes 25% of 8 later periods, mean +1.3% (holding ETH: 50%, mean +10.0%); over all history 52% (mean +7.0%) vs 52% (mean +26.5%) for just holding ETH; crypto: results hang on boom years; most passes disappear with $2 fees on $100
   #10 [breakout |EWT        |gate:none ] passed 6/8 of its own periods ($100: 3), mean +11.4%; seen in 2 of 12 runs; VERDICT LUCKY?
        Buys EWT on a new 5-day high, sells on a new 120-day low (breakout). Position 84% of the account, stop-loss 4%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +40% vs +43% for holding the market; passes in 18 years
        good: passes spread over 18 different years of history
        warnings: only 0 later periods to check; over all history 40% (mean +1.8%) vs 43% (mean +4.9%) for just holding EWT

3) LUCK BASELINE  (same system, same rules, on FAKE markets where the real returns were shuffled in blocks: no edge exists there)
   Hall of Fame top-10: average share of periods passed    real median 0.75 (runs 0.67..0.82) | fake markets median 0.70 (runs 0.68..0.75)
   Bots passing >= 60% of their periods (count)            real median 88 (runs 25..152) | fake markets median 96 (runs 45..118)
   All bot-periods that pass +6.5% (share)                 real median 0.07 (runs 0.05..0.08) | fake markets median 0.08 (runs 0.05..0.09)
   Frozen Ten portfolio: share of windows passing          real median 0.24 (runs 0.10..0.33) | fake markets median 0.33 (runs 0.24..0.48)
   Frozen Ten portfolio: mean 5-month return               real median +3.8% (runs +0.9%..+6.1%) | fake markets median +3.0% (runs +1.8%..+5.9%)
   Selection skill t-stat, holdout (above +3 = real)       real median +1.1 (runs +0.5..+1.8) | fake markets median +1.6 (runs +0.9..+2.7)

4) DOES NEWS HELP?  (same seeds, three settings)
   news + macro gates           Frozen Ten passes   24% of windows, mean +3.8% per 5m (-3.1% after $2 fees) | Hall-of-Fame top-10 pass rate 75% | all bot-periods passing 6.5% | selection t train +1.3, holdout +1.1
   macro gates only (no news)   Frozen Ten passes   26% of windows, mean +4.3% per 5m (-2.8% after $2 fees) | Hall-of-Fame top-10 pass rate 76% | all bot-periods passing 6.7% | selection t train +1.3, holdout +1.1
   no gates at all              Frozen Ten passes   24% of windows, mean +5.0% per 5m (-0.2% after $2 fees) | Hall-of-Fame top-10 pass rate 76% | all bot-periods passing 7.2% | selection t train +1.0, holdout +1.1
   Gate usage in the main variant: 55% of all bots ever born carry a gate; among Hall-of-Fame bots: 53% (top 30).

5) NEEDS YOUR ATTENTION
   CANDIDATES (kept passing after they were selected, beat just holding the market, spread over 4+ years, survive $2 fees): 1
     - [trend|ETH] Holds ETH while its 8-day average is above its 39-day average (trend following). Position 57% of the account, stop-loss 4%.  | later periods +50% of 12, all history +52% vs market +52%
   WATCH (decent but not proven): 0
   WARNING: 10 of the Hall-of-Fame top 10 look like luck (their record does not hold outside the periods they were picked on).

6) REPEAT OFFENDERS  (family x market combos where ALL bots of that type beat just holding the market, period after period, across every run; 405 combos tested, need t > 3.7)
   pairs     GBPUSD       54 periods  all-bot mean -0.1% vs holding -0.4% -> excess +0.3% per 5m (t=+0.4)  passes 0% of the time vs 11% for holding  
   reversion GBPUSD       54 periods  all-bot mean -0.3% vs holding -0.4% -> excess +0.2% per 5m (t=+0.3)  passes 0% of the time vs 11% for holding  
   tsmom     GBPUSD       54 periods  all-bot mean -0.4% vs holding -0.4% -> excess +0.0% per 5m (t=+0.0)  passes 0% of the time vs 11% for holding  
   reversion EURUSD       54 periods  all-bot mean -0.2% vs holding +0.0% -> excess -0.2% per 5m (t=-0.3)  passes 0% of the time vs 17% for holding  
   xsmom     GBPUSD       54 periods  all-bot mean -0.6% vs holding -0.4% -> excess -0.2% per 5m (t=-0.3)  passes 0% of the time vs 11% for holding  
   pairs     EURUSD       54 periods  all-bot mean -0.2% vs holding +0.0% -> excess -0.2% per 5m (t=-0.3)  passes 0% of the time vs 17% for holding  
   regime    NATGAS       54 periods  all-bot mean +2.9% vs holding +4.1% -> excess -1.2% per 5m (t=-0.3)  passes 22% of the time vs 43% for holding  
   breakout  EURUSD       54 periods  all-bot mean -0.2% vs holding +0.0% -> excess -0.3% per 5m (t=-0.4)  passes 0% of the time vs 17% for holding  
   trend     EURUSD       54 periods  all-bot mean -0.2% vs holding +0.0% -> excess -0.3% per 5m (t=-0.4)  passes 1% of the time vs 17% for holding  
   tsmom     EURUSD       54 periods  all-bot mean -0.3% vs holding +0.0% -> excess -0.3% per 5m (t=-0.4)  passes 0% of the time vs 17% for holding  
   Combos clearing the bar: 0 of 405.  (With 405 tries, a few at t>2.5 are expected by luck alone.)

7) WHICH 5-MONTH PERIODS PRODUCE PASSES  (share of ALL bots passing, per period, vs what markets did)
   from 2020-07-01: 25.5% of bots pass | S&P 500 +17.5%  Bitcoin +103.8%  average bot +9.3%
   from 2023-11-01: 23.5% of bots pass | S&P 500 +23.7%  Bitcoin +96.7%  average bot +8.5%
   from 2020-12-01: 21.3% of bots pass | S&P 500 +14.2%  Bitcoin +207.5%  average bot +14.3%
   from 2009-04-01: 19.5% of bots pass | S&P 500 +23.1%  Bitcoin n/a  average bot +3.3%
   from 2024-09-01: 18.6% of bots pass | S&P 500 +6.9%  Bitcoin +75.6%  average bot +4.8%
   from 2019-04-01: 18.2% of bots pass | S&P 500 +2.1%  Bitcoin +134.7%  average bot +6.1%
   from 2007-03-01: 17.2% of bots pass | S&P 500 +4.5%  Bitcoin n/a  average bot +3.0%
   from 2005-12-01: 16.7% of bots pass | S&P 500 +3.2%  Bitcoin n/a  average bot +2.6%
   Correlation between 'share of bots passing' and the S&P 500's return in that period: +0.55  (high = passes mostly ride the market)
   Most recent periods: 2024-04-01: 2.2% pass; 2024-09-01: 18.6% pass; 2025-02-01: 5.2% pass; 2025-07-01: 6.7% pass; 2025-12-01: 7.0% pass; 2026-05-01: 7.4% pass

Total time 111s