# Evolution research (standalone)

Never touches Supabase, the live agents or the dashboard. Manual GitHub workflows only.

| File | What it does |
|---|---|
| `engine.py` | 1,000 bots, 9 strategy families, 45 markets, 5-month generations from 1998. Optional "gates": a bot can step aside when a macro or news input is extreme. |
| `run.py` | **Test A** (widened search): Frozen Ten, Hall of Fame, luck baseline on shuffled fake markets, news on/off comparison, repeat offenders, which periods produce passes. |
| `scan.py` | **Test B** (gap scanner): 10 written ideas, one at a time, through the 6 gates. |
| `report.py` | Plain-English strategy text, verdicts (CANDIDATE / WATCH / LUCKY?), luck checks. |
| `news.py` | Point-in-time daily news counts from Wikipedia "Current events" (page exactly as it stood at the end of each day, fixed word lists, no AI reading it). |
| `test_engine.py` | Self-tests: no peeking at the future (prices AND news), random market finds nothing, planted edge is found, planted news signal is used. |
| `probe.py` | Checks that data sources are reachable and how fast. |

Pass rule: a 5-month period passes if the bot returns >= +6.5% net of trading costs. A second count uses a $100 account with a flat $2 per trade.

Workflows: **Evolve News Download** (once), then **Evolve Research**. Results are committed to `research/evolution/results/`.
