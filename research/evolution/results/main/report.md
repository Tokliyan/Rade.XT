====================================================================================================
[main] TEST A: widened search. 45 markets, 9 strategy families, 12 runs per variant, 1,000 bots, 1998 -> 2026-11-23
Pass rule: >= +6.5% in a 5-month period, net of trading costs ($100 version: flat $2 per trade). Holdout = 2018-01 onward.
====================================================================================================

1) THE FROZEN TEN  (fair test: picked in Jan 2018 from older data only, then run untouched; headline run seed 1000, cull 0.1)
   21 five-month windows from 2018-01-01.  Ten-bot portfolio passes in 7 of 21 windows (on $100 with $2 fees: 7).  Mean per 5 months +14.0% (after $2 fees +9.1%); worst -15.8%, best +128.5%; total +603.2%.
   For comparison just holding the S&P 500 passes 8 of 21 (mean +5.4% per 5 months); an equal mix of all markets passes 5 (mean +4.6%).
   #1  [xsmom    |BTC        |gate:news ] passes  8/21 ($100:  8)  mean +16.9%  worst -33.7%  best +156.2%  holding that market passes 8/21
        Holds BTC while it ranks in the top 35% of all markets by 120-day return (rotation); steps aside when the 5-day average of conflict/war news is more than 1.5 std below its norm. Position 82% of the account, stop-loss 22%.
   #2  [tsmom    |BTC        |gate:none ] passes  7/21 ($100:  6)  mean +15.3%  worst -16.0%  best +134.9%  holding that market passes 8/21
        Holds BTC while its 138-day return is above -0.6% (momentum). Position 74% of the account, stop-loss 5%.
   #3  [tsmom    |BTC        |gate:none ] passes  7/21 ($100:  6)  mean +15.3%  worst -16.0%  best +134.9%  holding that market passes 8/21
        Holds BTC while its 138-day return is above -0.6% (momentum). Position 74% of the account, stop-loss 5%.
   #4  [tsmom    |BTC        |gate:none ] passes  7/21 ($100:  6)  mean +13.8%  worst -15.9%  best +126.0%  holding that market passes 8/21
        Holds BTC while its 138-day return is above -1.6% (momentum). Position 70% of the account, stop-loss 4%.
   #5  [trend    |BTC        |gate:none ] passes  6/21 ($100:  6)  mean +13.3%  worst -11.4%  best +126.0%  holding that market passes 8/21
        Holds BTC while its 112-day average is above its 520-day average (trend following). Position 70% of the account, stop-loss 7%.
   #6  [xsmom    |BTC        |gate:news ] passes  8/21 ($100:  7)  mean +13.9%  worst -29.5%  best +126.3%  holding that market passes 8/21
        Holds BTC while it ranks in the top 22% of all markets by 120-day return (rotation); steps aside when the 5-day average of conflict/war news is more than 1.5 std below its norm. Position 71% of the account, stop-loss 22%.
   #7  [xsmom    |BTC        |gate:news ] passes  8/21 ($100:  7)  mean +13.9%  worst -29.5%  best +126.3%  holding that market passes 8/21
        Holds BTC while it ranks in the top 22% of all markets by 120-day return (rotation); steps aside when the 5-day average of conflict/war news is more than 1.5 std below its norm. Position 71% of the account, stop-loss 22%.
   #8  [breakout |BTC        |gate:none ] passes  8/21 ($100:  8)  mean +12.3%  worst -35.1%  best +119.9%  holding that market passes 8/21
        Buys BTC on a new 60-day high, sells on a new 120-day low (breakout). Position 68% of the account, stop-loss 24%.
   #9  [breakout |BTC        |gate:none ] passes  7/21 ($100:  7)  mean +13.7%  worst -35.1%  best +119.9%  holding that market passes 8/21
        Buys BTC on a new 100-day high, sells on a new 120-day low (breakout). Position 68% of the account, stop-loss 24%.
   #10 [trend    |BTC        |gate:none ] passes  6/21 ($100:  6)  mean +11.9%  worst -10.5%  best +114.2%  holding that market passes 8/21
        Holds BTC while its 120-day average is above its 557-day average (trend following). Position 65% of the account, stop-loss 8%.

   Across all 12 runs, the Frozen Ten portfolio passes 33% of windows (median; range 29% to 33%); mean per 5 months +9.4%; after $2 fees +1.4%.

2) HALL OF FAME  (hindsight list: the bots with the best pass record over their own lives, pooled over 12 runs; expect luck in here)
   #1  [trend    |EWZ        |gate:none ] passed 6/6 of its own periods ($100: 4), mean +15.6%; seen in 4 of 12 runs; VERDICT LUCKY?
        Holds EWZ while its 25-day average is above its 52-day average (trend following). Position 70% of the account, stop-loss 7%.
        checks: after selection +18% of 50 later periods pass (mean +0.8%); all history +26% vs +50% for holding the market; passes in 10 years
        good: passes spread over 10 different years of history
        warnings: after selection it passes 18% of 50 later periods, mean +0.8% (holding EWZ: 46%, mean +4.2%); over all history 26% (mean +2.3%) vs 50% (mean +6.0%) for just holding EWZ; makes very few trades per period, so little evidence
   #2  [trend    |EWY        |gate:macro] passed 4/4 of its own periods ($100: 2), mean +19.0%; seen in 2 of 12 runs; VERDICT LUCKY?
        Holds EWY while its 11-day average is above its 47-day average (trend following); steps aside when the 5-day average of the yield-curve slope (10yr minus 3-month) is more than 1.6 std below its norm. Position 70% of the account, stop-loss 25%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +25% vs +44% for holding the market; passes in 10 years
        good: passes spread over 10 different years of history
        warnings: only 0 later periods to check; over all history 25% (mean +1.6%) vs 44% (mean +6.5%) for just holding EWY
   #3  [xsmom    |EWY        |gate:news ] passed 4/4 of its own periods ($100: 1), mean +13.7%; seen in 3 of 12 runs; VERDICT LUCKY?
        Holds EWY while it ranks in the top 47% of all markets by 20-day return (rotation); steps aside when today's reading of interest-rate/inflation news is more than 1.1 std below its norm. Position 71% of the account, stop-loss 5%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +25% vs +44% for holding the market; passes in 12 years
        good: passes spread over 12 different years of history
        warnings: only 0 later periods to check; over all history 25% (mean -0.4%) vs 44% (mean +6.5%) for just holding EWY; most passes disappear with $2 fees on $100
   #4  [pairs    |XLE        |gate:none ] passed 4/4 of its own periods ($100: 0), mean +9.5%; seen in 1 of 12 runs; VERDICT LUCKY?
        Buys XLE when it lags EWY by 1.0 standard deviations over 18 days, sells when the gap closes to +0.7 (relative value). Position 100% of the account, stop-loss 15%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +12% vs +52% for holding the market; passes in 6 years
        good: passes spread over 6 different years of history
        warnings: only 0 later periods to check; over all history 12% (mean +1.2%) vs 52% (mean +4.9%) for just holding XLE; most passes disappear with $2 fees on $100
   #5  [breakout |EWZ        |gate:none ] passed 11/15 of its own periods ($100: 9), mean +12.3%; seen in 10 of 12 runs; VERDICT LUCKY?
        Buys EWZ on a new 25-day high, sells on a new 80-day low (breakout). Position 92% of the account, stop-loss 25%.
        checks: after selection +33% of 39 later periods pass (mean +1.9%); all history +47% vs +50% for holding the market; passes in 21 years
        good: passes spread over 21 different years of history
        warnings: after selection it passes 33% of 39 later periods, mean +1.9% (holding EWZ: 41%, mean +2.0%); over all history 47% (mean +5.4%) vs 50% (mean +6.0%) for just holding EWZ; makes very few trades per period, so little evidence
   #6  [pairs    |NATGAS     |gate:macro] passed 5/6 of its own periods ($100: 1), mean +12.3%; seen in 1 of 12 runs; VERDICT LUCKY?
        Buys NATGAS when it lags IEF by 1.0 standard deviations over 16 days, sells when the gap closes to +0.0 (relative value); steps aside when the 20-day average of the VIX fear index is more than 0.7 std below its norm. Position 95% of the account, stop-loss 25%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +29% vs +44% for holding the market; passes in 13 years
        good: passes spread over 13 different years of history
        warnings: only 0 later periods to check; over all history 29% (mean +2.6%) vs 44% (mean +4.9%) for just holding NATGAS; most passes disappear with $2 fees on $100
   #7  [breakout |EWW        |gate:news ] passed 5/6 of its own periods ($100: 4), mean +10.6%; seen in 3 of 12 runs; VERDICT LUCKY?
        Buys EWW on a new 8-day high, sells on a new 150-day low (breakout); steps aside when the 5-day average of oil/energy news is more than 0.5 std below its norm. Position 91% of the account, stop-loss 7%.
        checks: after selection +33% of 45 later periods pass (mean +0.8%); all history +39% vs +45% for holding the market; passes in 19 years
        good: passes spread over 19 different years of history
        warnings: after selection it passes 33% of 45 later periods, mean +0.8% (holding EWW: 42%, mean +3.0%); over all history 39% (mean +2.0%) vs 45% (mean +4.6%) for just holding EWW; makes very few trades per period, so little evidence
   #8  [xsmom    |XLE        |gate:news ] passed 5/6 of its own periods ($100: 3), mean +7.8%; seen in 2 of 12 runs; VERDICT LUCKY?
        Holds XLE while it ranks in the top 24% of all markets by 120-day return (rotation); steps aside when the 5-day average of oil/energy news is more than 1.1 std above its norm. Position 99% of the account, stop-loss 5%.
        checks: after selection +14% of 49 later periods pass (mean -0.8%); all history +18% vs +52% for holding the market; passes in 9 years
        good: passes spread over 9 different years of history
        warnings: after selection it passes 14% of 49 later periods, mean -0.8% (holding XLE: 47%, mean +4.2%); over all history 18% (mean -0.5%) vs 52% (mean +4.9%) for just holding XLE
   #9  [voltiming|EWZ        |gate:none ] passed 8/11 of its own periods ($100: 7), mean +12.9%; seen in 2 of 12 runs; VERDICT LUCKY?
        Holds EWZ only while its 51-day volatility is under 32% a year and it is in an uptrend (calm-market timing). Position 90% of the account, stop-loss 15%.
        checks: after selection +15% of 46 later periods pass (mean -0.9%); all history +26% vs +50% for holding the market; passes in 10 years
        good: passes spread over 10 different years of history
        warnings: after selection it passes 15% of 46 later periods, mean -0.9% (holding EWZ: 43%, mean +3.0%); over all history 26% (mean +1.7%) vs 50% (mean +6.0%) for just holding EWZ
   #10 [calendar |ETH        |gate:news ] passed 9/13 of its own periods ($100: 4), mean +13.8%; seen in 6 of 12 runs; VERDICT LUCKY?
        Holds ETH over the last 6 and first 0 trading days of each month (calendar); steps aside when the 5-day average of health/pandemic news is more than 2.0 std above its norm. Position 97% of the account, stop-loss 4%.
        checks: after selection +0% of 5 later periods pass (mean -6.9%); all history +48% vs +52% for holding the market; passes in 5 years
        warnings: only 5 later periods to check; over all history 48% (mean +7.3%) vs 52% (mean +26.5%) for just holding ETH; passes come from only 5 different year(s) of history; crypto: results hang on boom years; most passes disappear with $2 fees on $100

3) LUCK BASELINE  (same system, same rules, on FAKE markets where the real returns were shuffled in blocks: no edge exists there)
   Hall of Fame top-10: average share of periods passed    real median 0.75 (runs 0.66..0.88) | fake markets median 0.73 (runs 0.68..0.81)
   Bots passing >= 60% of their periods (count)            real median 83 (runs 46..188) | fake markets median 93 (runs 50..170)
   All bot-periods that pass +6.5% (share)                 real median 0.07 (runs 0.06..0.08) | fake markets median 0.07 (runs 0.06..0.08)
   Frozen Ten portfolio: share of windows passing          real median 0.33 (runs 0.29..0.33) | fake markets median 0.31 (runs 0.10..0.43)
   Frozen Ten portfolio: mean 5-month return               real median +9.4% (runs +5.1%..+14.0%) | fake markets median +2.4% (runs +1.2%..+4.6%)
   Selection skill t-stat, holdout (above +3 = real)       real median +1.1 (runs +0.9..+1.5) | fake markets median +1.5 (runs -1.5..+1.9)

4) DOES NEWS HELP?  (same seeds, three settings)
   news + macro gates           Frozen Ten passes   33% of windows, mean +9.4% per 5m (+1.4% after $2 fees) | Hall-of-Fame top-10 pass rate 75% | all bot-periods passing 7.5% | selection t train +1.7, holdout +1.1
   macro gates only (no news)   Frozen Ten passes   29% of windows, mean +9.6% per 5m (+1.6% after $2 fees) | Hall-of-Fame top-10 pass rate 75% | all bot-periods passing 6.5% | selection t train +1.8, holdout +1.0
   no gates at all              Frozen Ten passes   29% of windows, mean +9.7% per 5m (+2.2% after $2 fees) | Hall-of-Fame top-10 pass rate 75% | all bot-periods passing 7.1% | selection t train +1.5, holdout +1.1
   Gate usage in the main variant: 55% of all bots ever born carry a gate; among Hall-of-Fame bots: 60% (top 30).

5) NEEDS YOUR ATTENTION
   CANDIDATES (kept passing after they were selected, beat just holding the market, spread over 4+ years, survive $2 fees): 1
     - [regime|ETH] Holds ETH all the time (risk-off timing); steps aside when the 20-day average of health/pandemic news is more than 0.6 std above its norm. Position 91% of the account, stop-loss 4%.  | later periods +42% of 12, all history +52% vs market +52%
   WATCH (decent but not proven): 0
   WARNING: 10 of the Hall-of-Fame top 10 look like luck (their record does not hold outside the periods they were picked on).

6) REPEAT OFFENDERS  (family x market combos where ALL bots of that type beat just holding the market, period after period, across every run; 405 combos tested, need t > 3.7)
   reversion GBPUSD       54 periods  all-bot mean -0.2% vs holding -0.4% -> excess +0.3% per 5m (t=+0.4)  passes 0% of the time vs 11% for holding  
   pairs     GBPUSD       54 periods  all-bot mean -0.2% vs holding -0.4% -> excess +0.2% per 5m (t=+0.3)  passes 0% of the time vs 11% for holding  
   tsmom     GBPUSD       54 periods  all-bot mean -0.4% vs holding -0.4% -> excess +0.1% per 5m (t=+0.1)  passes 0% of the time vs 11% for holding  
   reversion EURUSD       54 periods  all-bot mean -0.1% vs holding +0.0% -> excess -0.2% per 5m (t=-0.2)  passes 0% of the time vs 17% for holding  
   trend     GBPUSD       54 periods  all-bot mean -0.6% vs holding -0.4% -> excess -0.2% per 5m (t=-0.2)  passes 0% of the time vs 11% for holding  
   pairs     AUDUSD       48 periods  all-bot mean -0.2% vs holding +0.2% -> excess -0.4% per 5m (t=-0.3)  passes 0% of the time vs 19% for holding  
   pairs     EURUSD       54 periods  all-bot mean -0.2% vs holding +0.0% -> excess -0.3% per 5m (t=-0.3)  passes 0% of the time vs 17% for holding  
   xsmom     GBPUSD       54 periods  all-bot mean -0.7% vs holding -0.4% -> excess -0.2% per 5m (t=-0.3)  passes 1% of the time vs 11% for holding  
   trend     EURUSD       54 periods  all-bot mean -0.2% vs holding +0.0% -> excess -0.3% per 5m (t=-0.4)  passes 1% of the time vs 17% for holding  
   breakout  EURUSD       54 periods  all-bot mean -0.3% vs holding +0.0% -> excess -0.3% per 5m (t=-0.4)  passes 1% of the time vs 17% for holding  
   Combos clearing the bar: 0 of 405.  (With 405 tries, a few at t>2.5 are expected by luck alone.)

7) WHICH 5-MONTH PERIODS PRODUCE PASSES  (share of ALL bots passing, per period, vs what markets did)
   from 2020-07-01: 29.5% of bots pass | S&P 500 +17.5%  Bitcoin +103.8%  average bot +11.5%
   from 2023-11-01: 26.7% of bots pass | S&P 500 +23.7%  Bitcoin +96.7%  average bot +10.4%
   from 2020-12-01: 26.6% of bots pass | S&P 500 +14.2%  Bitcoin +207.5%  average bot +20.1%
   from 2024-09-01: 21.4% of bots pass | S&P 500 +6.9%  Bitcoin +75.6%  average bot +5.2%
   from 2005-12-01: 20.9% of bots pass | S&P 500 +3.2%  Bitcoin n/a  average bot +3.2%
   from 2019-04-01: 20.3% of bots pass | S&P 500 +2.1%  Bitcoin +134.7%  average bot +7.5%
   from 2009-04-01: 19.6% of bots pass | S&P 500 +23.1%  Bitcoin n/a  average bot +3.1%
   from 2006-10-02: 18.0% of bots pass | S&P 500 +5.4%  Bitcoin n/a  average bot +2.5%
   Correlation between 'share of bots passing' and the S&P 500's return in that period: +0.51  (high = passes mostly ride the market)
   Most recent periods: 2024-04-01: 1.8% pass; 2024-09-01: 21.4% pass; 2025-02-01: 5.7% pass; 2025-07-01: 7.4% pass; 2025-12-01: 8.2% pass; 2026-05-01: 6.8% pass

Total time 206s