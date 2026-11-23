====================================================================================================
[no_crypto] TEST A: widened search. 43 markets, 9 strategy families, 12 runs per variant, 1,000 bots, 1998 -> 2026-11-23
Pass rule: >= +6.5% in a 5-month period, net of trading costs ($100 version: flat $2 per trade). Holdout = 2018-01 onward.
====================================================================================================

1) THE FROZEN TEN  (fair test: picked in Jan 2018 from older data only, then run untouched; headline run seed 1000, cull 0.1)
   21 five-month windows from 2018-01-01.  Ten-bot portfolio passes in 8 of 21 windows (on $100 with $2 fees: 5).  Mean per 5 months +4.2% (after $2 fees -2.2%); worst -8.5%, best +21.3%; total +121.6%.
   For comparison just holding the S&P 500 passes 8 of 21 (mean +5.4% per 5 months); an equal mix of all markets passes 6 (mean +3.7%).
   #1  [trend    |BOVESPA    |gate:news ] passes  4/21 ($100:  0)  mean +2.1%  worst -6.1%  best +20.3%  holding that market passes 11/21
        Holds BOVESPA while its 10-day average is above its 17-day average (trend following); steps aside when the 20-day average of oil/energy news is more than 0.8 std above its norm. Position 93% of the account, stop-loss 6%.
   #2  [tsmom    |XLK        |gate:none ] passes  9/21 ($100:  8)  mean +3.8%  worst -26.9%  best +24.4%  holding that market passes 13/21
        Holds XLK while its 241-day return is above -1.4% (momentum). Position 99% of the account, stop-loss 4%.
   #3  [tsmom    |XLK        |gate:none ] passes 10/21 ($100:  7)  mean +5.5%  worst -7.7%  best +24.4%  holding that market passes 13/21
        Holds XLK while its 230-day return is above -1.1% (momentum). Position 99% of the account, stop-loss 4%.
   #4  [regime   |XLK        |gate:macro] passes  9/21 ($100:  9)  mean +4.9%  worst -14.5%  best +29.3%  holding that market passes 13/21
        Holds XLK all the time (risk-off timing); steps aside when the 5-day average of a jump in the VIX is more than 1.9 std below its norm. Position 92% of the account, stop-loss 12%.
   #5  [regime   |XLK        |gate:macro] passes  9/21 ($100:  9)  mean +4.9%  worst -14.5%  best +29.3%  holding that market passes 13/21
        Holds XLK all the time (risk-off timing); steps aside when the 5-day average of a jump in the VIX is more than 1.9 std below its norm. Position 92% of the account, stop-loss 12%.
   #6  [regime   |XLK        |gate:news ] passes  9/21 ($100:  7)  mean +4.0%  worst -17.3%  best +25.1%  holding that market passes 13/21
        Holds XLK all the time (risk-off timing); steps aside when the 5-day average of conflict/war news is more than 1.7 std below its norm. Position 80% of the account, stop-loss 15%.
   #7  [xsmom    |XLK        |gate:none ] passes  7/21 ($100:  5)  mean +3.5%  worst -8.5%  best +24.7%  holding that market passes 13/21
        Holds XLK while it ranks in the top 27% of all markets by 250-day return (rotation). Position 100% of the account, stop-loss 7%.
   #8  [xsmom    |XLK        |gate:none ] passes  7/21 ($100:  5)  mean +3.7%  worst -14.2%  best +24.7%  holding that market passes 13/21
        Holds XLK while it ranks in the top 27% of all markets by 250-day return (rotation). Position 100% of the account, stop-loss 8%.
   #9  [xsmom    |XLK        |gate:news ] passes  6/21 ($100:  3)  mean +3.6%  worst -8.8%  best +24.7%  holding that market passes 13/21
        Holds XLK while it ranks in the top 27% of all markets by 250-day return (rotation); steps aside when today's reading of health/pandemic news is more than 0.5 std below its norm. Position 100% of the account, stop-loss 8%.
   #10 [breakout |XLK        |gate:none ] passes 12/21 ($100:  7)  mean +6.1%  worst -19.3%  best +29.1%  holding that market passes 13/21
        Buys XLK on a new 10-day high, sells on a new 80-day low (breakout). Position 93% of the account, stop-loss 7%.

   Across all 12 runs, the Frozen Ten portfolio passes 19% of windows (median; range 10% to 38%); mean per 5 months +1.5%; after $2 fees -3.3%.

2) HALL OF FAME  (hindsight list: the bots with the best pass record over their own lives, pooled over 12 runs; expect luck in here)
   #1  [breakout |EWZ        |gate:news ] passed 8/9 of its own periods ($100: 8), mean +12.7%; seen in 8 of 12 runs; VERDICT LUCKY?
        Buys EWZ on a new 10-day high, sells on a new 200-day low (breakout); steps aside when the 5-day average of oil/energy news is more than 2.0 std above its norm. Position 56% of the account, stop-loss 12%.
        checks: after selection +27% of 44 later periods pass (mean +1.4%); all history +39% vs +50% for holding the market; passes in 17 years
        good: passes spread over 17 different years of history
        warnings: after selection it passes 27% of 44 later periods, mean +1.4% (holding EWZ: 41%, mean +1.9%); over all history 39% (mean +3.3%) vs 50% (mean +6.0%) for just holding EWZ; makes very few trades per period, so little evidence
   #2  [tsmom    |EWY        |gate:news ] passed 4/4 of its own periods ($100: 4), mean +26.7%; seen in 5 of 12 runs; VERDICT LUCKY?
        Holds EWY while its 174-day return is above 7.6% (momentum); steps aside when the 20-day average of financial-crisis news is more than 1.8 std above its norm. Position 78% of the account, stop-loss 14%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +25% vs +44% for holding the market; passes in 10 years
        good: passes spread over 10 different years of history
        warnings: only 0 later periods to check; over all history 25% (mean +2.3%) vs 44% (mean +6.5%) for just holding EWY; makes very few trades per period, so little evidence
   #3  [voltiming|KOSPI      |gate:none ] passed 4/4 of its own periods ($100: 2), mean +17.6%; seen in 2 of 12 runs; VERDICT LUCKY?
        Holds KOSPI only while its 31-day volatility is under 28% a year (calm-market timing). Position 95% of the account, stop-loss 6%.
        checks: after selection n/a of 0 later periods pass (mean n/a); all history +30% vs +41% for holding the market; passes in 13 years
        good: passes spread over 13 different years of history
        warnings: only 0 later periods to check; over all history 30% (mean +2.8%) vs 41% (mean +6.0%) for just holding KOSPI
   #4  [calendar |KOSPI      |gate:none ] passed 6/7 of its own periods ($100: 1), mean +18.6%; seen in 3 of 12 runs; VERDICT LUCKY?
        Holds KOSPI over the last 4 and first 6 trading days of each month (calendar). Position 91% of the account, stop-loss 2%.
        checks: after selection +13% of 62 later periods pass (mean -1.2%); all history +20% vs +41% for holding the market; passes in 10 years
        good: passes spread over 10 different years of history
        warnings: after selection it passes 13% of 62 later periods, mean -1.2% (holding KOSPI: 40%, mean +5.7%); over all history 20% (mean +0.8%) vs 41% (mean +6.0%) for just holding KOSPI; most passes disappear with $2 fees on $100
   #5  [trend    |XLE        |gate:none ] passed 6/7 of its own periods ($100: 6), mean +11.2%; seen in 3 of 12 runs; VERDICT LUCKY?
        Holds XLE while its 72-day average is above its 343-day average (trend following). Position 100% of the account, stop-loss 15%.
        checks: after selection +33% of 48 later periods pass (mean +3.1%); all history +36% vs +52% for holding the market; passes in 15 years
        good: passes spread over 15 different years of history
        warnings: after selection it passes 33% of 48 later periods, mean +3.1% (holding XLE: 48%, mean +4.5%); over all history 36% (mean +3.5%) vs 52% (mean +4.9%) for just holding XLE; makes very few trades per period, so little evidence
   #6  [voltiming|XLV        |gate:news ] passed 6/7 of its own periods ($100: 5), mean +7.9%; seen in 5 of 12 runs; VERDICT LUCKY?
        Holds XLV only while its 44-day volatility is under 40% a year (calm-market timing); steps aside when the 20-day average of how much news there is is more than 1.7 std above its norm. Position 97% of the account, stop-loss 6%.
        checks: after selection +31% of 26 later periods pass (mean +1.5%); all history +35% vs +38% for holding the market; passes in 17 years
        good: passes spread over 17 different years of history
        warnings: after selection it passes 31% of 26 later periods, mean +1.5% (holding XLV: 31%, mean +4.2%); over all history 35% (mean +2.0%) vs 38% (mean +3.8%) for just holding XLV; makes very few trades per period, so little evidence
   #7  [voltiming|EWZ        |gate:none ] passed 7/9 of its own periods ($100: 4), mean +8.6%; seen in 3 of 12 runs; VERDICT LUCKY?
        Holds EWZ only while its 49-day volatility is under 32% a year (calm-market timing). Position 61% of the account, stop-loss 6%.
        checks: after selection +10% of 48 later periods pass (mean -0.7%); all history +19% vs +50% for holding the market; passes in 8 years
        good: passes spread over 8 different years of history
        warnings: after selection it passes 10% of 48 later periods, mean -0.7% (holding EWZ: 46%, mean +4.0%); over all history 19% (mean +0.5%) vs 50% (mean +6.0%) for just holding EWZ
   #8  [breakout |GOLD       |gate:none ] passed 5/6 of its own periods ($100: 3), mean +9.5%; seen in 1 of 12 runs; VERDICT LUCKY?
        Buys GOLD on a new 80-day high, sells on a new 80-day low (breakout). Position 87% of the account, stop-loss 24%.
        checks: after selection +0% of 1 later periods pass (mean -9.4%); all history +23% vs +39% for holding the market; passes in 10 years
        good: passes spread over 10 different years of history
        warnings: only 1 later periods to check; over all history 23% (mean +1.7%) vs 39% (mean +5.0%) for just holding GOLD; makes very few trades per period, so little evidence
   #9  [breakout |EWW        |gate:news ] passed 5/6 of its own periods ($100: 3), mean +9.4%; seen in 3 of 12 runs; VERDICT LUCKY?
        Buys EWW on a new 8-day high, sells on a new 50-day low (breakout); steps aside when today's reading of tariff/sanctions news is more than 2.3 std below its norm. Position 89% of the account, stop-loss 11%.
        checks: after selection +29% of 45 later periods pass (mean +0.5%); all history +35% vs +45% for holding the market; passes in 18 years
        good: passes spread over 18 different years of history
        warnings: after selection it passes 29% of 45 later periods, mean +0.5% (holding EWW: 42%, mean +3.0%); over all history 35% (mean +1.3%) vs 45% (mean +4.6%) for just holding EWW
   #10 [regime   |SHANGHAI   |gate:news ] passed 8/11 of its own periods ($100: 6), mean +12.0%; seen in 4 of 12 runs; VERDICT LUCKY?
        Holds SHANGHAI all the time (risk-off timing); steps aside when today's reading of interest-rate/inflation news is more than 1.7 std below its norm. Position 70% of the account, stop-loss 18%.
        checks: after selection +18% of 39 later periods pass (mean +0.8%); all history +30% vs +36% for holding the market; passes in 17 years
        good: passes spread over 17 different years of history
        warnings: after selection it passes 18% of 39 later periods, mean +0.8% (holding SHANGHAI: 26%, mean +1.9%); over all history 30% (mean +2.4%) vs 36% (mean +3.5%) for just holding SHANGHAI; makes very few trades per period, so little evidence

3) LUCK BASELINE  (same system, same rules, on FAKE markets where the real returns were shuffled in blocks: no edge exists there)
   Hall of Fame top-10: average share of periods passed    real median 0.78 (runs 0.64..0.80) | fake markets median 0.70 (runs 0.68..0.78)
   Bots passing >= 60% of their periods (count)            real median 70 (runs 19..184) | fake markets median 60 (runs 36..93)
   All bot-periods that pass +6.5% (share)                 real median 0.06 (runs 0.04..0.07) | fake markets median 0.06 (runs 0.05..0.09)
   Frozen Ten portfolio: share of windows passing          real median 0.19 (runs 0.10..0.38) | fake markets median 0.29 (runs 0.24..0.29)
   Frozen Ten portfolio: mean 5-month return               real median +1.5% (runs +0.2%..+4.2%) | fake markets median +2.9% (runs +2.2%..+3.7%)
   Selection skill t-stat, holdout (above +3 = real)       real median +0.2 (runs -0.4..+1.7) | fake markets median +0.9 (runs -0.3..+1.9)

4) DOES NEWS HELP?  (same seeds, three settings)
   news + macro gates           Frozen Ten passes   19% of windows, mean +1.5% per 5m (-3.3% after $2 fees) | Hall-of-Fame top-10 pass rate 78% | all bot-periods passing 5.7% | selection t train +0.8, holdout +0.2
   macro gates only (no news)   Frozen Ten passes   14% of windows, mean +0.9% per 5m (-5.1% after $2 fees) | Hall-of-Fame top-10 pass rate 74% | all bot-periods passing 5.3% | selection t train +0.6, holdout +0.7
   no gates at all              Frozen Ten passes   19% of windows, mean +1.6% per 5m (-2.7% after $2 fees) | Hall-of-Fame top-10 pass rate 75% | all bot-periods passing 5.1% | selection t train +0.7, holdout +0.8
   Gate usage in the main variant: 53% of all bots ever born carry a gate; among Hall-of-Fame bots: 60% (top 30).

5) NEEDS YOUR ATTENTION
   CANDIDATES (kept passing after they were selected, beat just holding the market, spread over 4+ years, survive $2 fees): 0
   WATCH (decent but not proven): 0
   WARNING: 10 of the Hall-of-Fame top 10 look like luck (their record does not hold outside the periods they were picked on).

6) REPEAT OFFENDERS  (family x market combos where ALL bots of that type beat just holding the market, period after period, across every run; 387 combos tested, need t > 3.7)
   pairs     GBPUSD       54 periods  all-bot mean -0.2% vs holding -0.4% -> excess +0.3% per 5m (t=+0.4)  passes 0% of the time vs 11% for holding  
   reversion GBPUSD       54 periods  all-bot mean -0.2% vs holding -0.4% -> excess +0.2% per 5m (t=+0.3)  passes 0% of the time vs 11% for holding  
   tsmom     GBPUSD       54 periods  all-bot mean -0.2% vs holding -0.4% -> excess +0.2% per 5m (t=+0.3)  passes 0% of the time vs 11% for holding  
   xsmom     GBPUSD       54 periods  all-bot mean -0.4% vs holding -0.4% -> excess -0.0% per 5m (t=-0.0)  passes 0% of the time vs 11% for holding  
   trend     GBPUSD       54 periods  all-bot mean -0.5% vs holding -0.4% -> excess -0.1% per 5m (t=-0.1)  passes 0% of the time vs 11% for holding  
   tsmom     AUDUSD       48 periods  all-bot mean -0.0% vs holding +0.2% -> excess -0.2% per 5m (t=-0.2)  passes 3% of the time vs 19% for holding  
   reversion EURUSD       54 periods  all-bot mean -0.2% vs holding +0.0% -> excess -0.2% per 5m (t=-0.2)  passes 0% of the time vs 17% for holding  
   pairs     EURUSD       54 periods  all-bot mean -0.2% vs holding +0.0% -> excess -0.2% per 5m (t=-0.3)  passes 0% of the time vs 17% for holding  
   voltiming GBPUSD       54 periods  all-bot mean -0.6% vs holding -0.4% -> excess -0.2% per 5m (t=-0.3)  passes 2% of the time vs 11% for holding  
   breakout  GBPUSD       54 periods  all-bot mean -0.7% vs holding -0.4% -> excess -0.2% per 5m (t=-0.3)  passes 0% of the time vs 11% for holding  
   Combos clearing the bar: 0 of 387.  (With 387 tries, a few at t>2.5 are expected by luck alone.)

7) WHICH 5-MONTH PERIODS PRODUCE PASSES  (share of ALL bots passing, per period, vs what markets did)
   from 2005-12-01: 22.6% of bots pass | S&P 500 +3.2%  Bitcoin n/a  average bot +3.4%
   from 2009-04-01: 21.6% of bots pass | S&P 500 +23.1%  Bitcoin n/a  average bot +3.7%
   from 2007-03-01: 20.9% of bots pass | S&P 500 +4.5%  Bitcoin n/a  average bot +3.8%
   from 2006-10-02: 20.5% of bots pass | S&P 500 +5.4%  Bitcoin n/a  average bot +2.7%
   from 2010-07-01: 16.1% of bots pass | S&P 500 +17.4%  Bitcoin n/a  average bot +2.4%
   from 2011-10-03: 14.0% of bots pass | S&P 500 +25.0%  Bitcoin n/a  average bot +2.1%
   from 2005-07-01: 13.2% of bots pass | S&P 500 +5.9%  Bitcoin n/a  average bot +2.3%
   from 2007-08-01: 12.5% of bots pass | S&P 500 +0.2%  Bitcoin n/a  average bot +0.6%
   Correlation between 'share of bots passing' and the S&P 500's return in that period: +0.44  (high = passes mostly ride the market)
   Most recent periods: 2024-04-01: 1.8% pass; 2024-09-01: 2.7% pass; 2025-02-01: 3.5% pass; 2025-07-01: 8.9% pass; 2025-12-01: 7.3% pass; 2026-05-01: 5.5% pass

Total time 209s