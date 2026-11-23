# Evolution research (standalone)

1,000 bots evolve through daily market history from Jan 1998 to today.
Six strategy families (trend, mean-reversion, breakout, time-series momentum,
volatility timing, turn-of-month calendar) on 12 indices/commodities/FX/bonds/BTC.
Every 5 months: kill the worst, clone the best with mutation, add 5% random newcomers.
Islands (one per family) keep the population diverse. Bots die at -30% from peak.

Honest scoring: the headline is how SELECTED bots do in the NEXT period, plus a
frozen committee tested on a 2018-today holdout. Never the best bot's own score.

    cd research/evolution
    python test_engine.py                      # fake-market self-test
    python run.py --data real --seeds 6        # real history (needs internet)

Not connected to the live bots, Supabase or the dashboard.
