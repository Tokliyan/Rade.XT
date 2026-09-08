# Trading Bot — autonomous, multi-agent, free to run

Three independent paper-trading agents, each with its own strategy and
symbols, running unattended on a schedule and checkpointing their state
to Supabase between runs — so there's no server to keep on and nothing
you have to pay for.

**Read this whole file before running anything live. Automated trading can
lose real money quickly — the code runs exactly what you tell it to, with
no judgment of its own.**

## How the pieces fit

```
GitHub Actions (free cron)
        |
        v
  main.py --agent <name>   <-- one single "tick": fetch price, decide, trade, exit
        |
        v
     Supabase              <-- remembers cash/positions/pauses between runs
        |
        v
  dashboard.html            <-- you open this every couple of days to check in
```

| File | Purpose |
|---|---|
| `config.py` | Defines the 3 agents: symbols, strategy, risk settings, the global `PAPER_TRADING` switch |
| `strategy.py` | `SmaCrossStrategy` (trend-following) and `RsiMeanReversionStrategy` (bets on snap-backs) |
| `risk_manager.py` | Position sizing + stop-loss/take-profit |
| `broker.py` | `PaperBroker` (simulated fills), `LiveBroker` (guarded stub, unwired on purpose) |
| `state_store.py` | Reads/writes each agent's state and trade log to Supabase |
| `data_feed.py` | Live candles via ccxt, or synthetic data for offline testing |
| `backtester.py` / `demo_backtest.py` | Replay a strategy over historical (or synthetic) data |
| `main.py` | The single-tick runner GitHub Actions calls on a schedule |
| `.github/workflows/trading-bot.yml` | The free scheduler — runs all 3 agents every 30 min |
| `supabase_schema.sql` | Run once in Supabase to create the two tables |
| `dashboard.html` | Standalone check-in page — deploy on Netlify like leadlensai |

## The 3 agents it ships with

Split across genuinely different asset classes, not just different coins:

- **asx_bluechip_steady** — SMA crossover (trend-following) on CBA.AX,
  BHP.AX — large, established ASX companies. The "steady" bucket.
- **asx_smallcap_growth** — RSI mean-reversion on PLS.AX, LTR.AX — small,
  volatile ASX lithium miners. The closest honest stand-in for "IPO-style"
  high growth/high risk — literal pre-listing IPOs have no price history
  to trade on, so this uses small, newer-ish, high-volatility stocks
  instead of pretending to simulate something that isn't simulatable.
- **crypto_store_of_value** — SMA crossover on BTC/USDT, PAXG/USDT (a
  token backed 1:1 by physical gold) — the "hold value" bucket, both
  digital and physical, both on the same crypto pipeline as before.

Stock data comes free from Yahoo Finance via `yfinance` — no account, no
API key. Two things worth knowing: it's an unofficial wrapper so it's
occasionally flaky, and the ASX only trades ~10am-4pm AEST on weekdays —
outside those hours a stock agent's tick just sees the same last price
again and does nothing, which is harmless but means don't expect action
from the ASX agents overnight or on weekends.

Different strategy logic and/or different symbols per agent, each with
its own simulated balance, so you can compare which approach actually
holds up over time. Add a 4th by adding one more `AgentConfig` to
`config.py` — the scheduler and dashboard pick it up automatically once
you also add its name to the workflow's `matrix.agent` list.

## Setup (do this once)

1. **Supabase** — open your existing project's SQL editor and run
   `supabase_schema.sql`. Then grab two things from Project Settings → API:
   - the **service role key** (secret — write access, bypasses RLS)
   - the **anon public key** (safe to expose — read-only, per the schema's policies)

2. **GitHub repo** — push this project to a **public** GitHub repo (public =
   unlimited free Actions minutes; private repos get a limited free
   quota). No secrets are ever committed, so public is fine.
   In the repo's Settings → Secrets and variables → Actions, add:
   - `SUPABASE_URL` — your project URL
   - `SUPABASE_KEY` — the **service role** key from step 1

3. **Enable the workflow** — it starts running automatically on the cron
   schedule once it's on the default branch. You can also trigger it
   manually from the Actions tab any time ("Run workflow" button).
   
   One GitHub quirk worth knowing: scheduled workflows get disabled if a
   repo sees no commits for 60 days. Any small commit resets that clock.

4. **Dashboard** — open `dashboard.html`, fill in `SUPABASE_URL` and
   `SUPABASE_ANON_KEY` (the anon key from step 1, **not** the service
   key). No backend or server needed to host it — it's a static file
   that talks to Supabase directly from the browser. Cheapest path
   since the repo already exists: enable **GitHub Pages** (repo →
   Settings → Pages → Deploy from branch → `main` → `/`), which serves
   it free from the same repo with no extra signup. Netlify (like
   leadlensai) or Render's **Static Site** type work identically if you'd
   rather use those — just skip Render's "Create new service" flow,
   that's for long-running processes this doesn't have. Bookmark
   whichever URL you land on — that's your check-in page.

## Before you touch real money

1. **Backtest on real historical data, not just the synthetic demo.** Pull
   real candles (`data_feed.get_live_ohlcv`) or load a CSV you already have,
   and run `backtester.run_backtest` on a long, varied time period.
2. **Watch for overfitting.** If you tweak a strategy until backtest
   returns look amazing, you've probably just fit noise in that specific
   history. Test on data the strategy hasn't "seen."
3. **Let it paper trade for a real stretch of time** — weeks, not days —
   before ever considering flipping `PAPER_TRADING` to `False`.
4. **`LiveBroker` is deliberately unfinished.** Wiring real order-sending
   is left as a manual step — via `ccxt`'s `create_order()` for crypto
   exchanges, or a broker SDK like `alpaca-py` for stocks — tested against
   that exchange's sandbox/testnet endpoint first.
5. **Most exchanges/brokers require you to be 18+** to open an account and
   trade with real funds; a custodial account with a parent/guardian is
   the usual route otherwise.
6. **Nothing here is financial advice.** Both included strategies are
   templates to test and refine, not proven money-makers — the honest
   synthetic-data demo results (some agents up, some down) are the point:
   treat any backtest as a hypothesis, not a result to trust outright.

## Going live — the actual next steps, in order

**Only `crypto_store_of_value` has a live-execution path.** The two ASX
agents are paper-only for now — `main.py` will refuse to run either of
them live, since there's no real ASX broker wired up (that'd need a
separate Australian broker with API access, its own account, and its own
integration work — a real project on its own, not started here).

1. **Finish and run the paper setup above first.** Everything below builds
   on top of it — same agents, same Supabase, same dashboard.

2. **Testnet next — costs nothing, needs no account verification.**
   Sign up free at your exchange's sandbox — for Binance,
   testnet.binance.vision — and generate a testnet API key (fake balance,
   real order mechanics). Add it to GitHub Secrets as `EXCHANGE_API_KEY` /
   `EXCHANGE_API_SECRET`, then set `PAPER_TRADING = False` in `config.py`
   (leave `LIVE_SANDBOX = True`). Push. This proves the whole "fully
   automated, actually placing orders" pipeline end to end, with zero
   money and zero age/KYC restriction.

3. **Real money is a separate, later decision — gated on purpose.** When
   (if) you get there: you'll need a verified 18+ account, or a parent
   holding one on your behalf. Generate a real API key with **TRADE
   permissions only — never enable withdrawal** on it, so a leaked key
   can't drain funds, only trade badly. Set `LIVE_SANDBOX = False` and the
   `CONFIRM_LIVE_TRADING` GitHub secret to exactly `YES-I-UNDERSTAND` —
   three separate switches have to agree before a single real order goes
   out. Start with an amount you'd be fine losing entirely, because that's
   the realistic range of outcomes for an unproven strategy.

`MAX_LIVE_ORDER_USD` in `config.py` (default $20) is a hard ceiling on any
single live order regardless of what the risk manager calculates — a second,
blunter safety net for a first real deployment. Raise it only once you've
watched it behave correctly for a while.

## Market conditions, historical ranges, and risk profiles

Three additions on top of the original setup:

- **Market conditions** — each agent card shows the live price and %
  change for its symbols, pulled fresh every tick. For the ASX agents
  this also notes when the market's closed, since outside ~10am-4pm AEST
  weekdays you're just seeing the last traded price.
- **Historical range** — instead of a fake "projected value," each card
  shows the real spread of outcomes when this exact strategy was replayed
  over actual past price data in overlapping 14-day windows (e.g. "-13%
  to +11%, typical -1%, n=48 windows"). This is honest history, explicitly
  not a prediction — a strategy that ranged wildly in the past will very
  likely keep doing so, and a narrow historical range is not a promise
  either. Computed by `backtest_stats.py`, refreshed weekly by its own
  workflow (`.github/workflows/backtest-stats.yml`).
- **Risk profile buttons** — Safe / Balanced / All-in on each card, live
  from the dashboard. Safe halves the normal bet size and tightens stops.
  All-in concentrates into a single symbol and risks far more per trade —
  a real "bet it all" mode, not a cosmetic label. One thing that does NOT
  change: a daily circuit breaker always exists, even in All-in mode (just
  with a higher ceiling — 20% instead of the normal 8%). Read fresh at the
  start of every tick, so a change takes effect within one run, no
  redeploy needed.

### Extra one-time setup for this part

1. **Run the updated `supabase_schema.sql` again** — it's additive
   (`if not exists` throughout), safe to re-run on a project that already
   has the original tables. This adds `agent_settings`, `backtest_stats`,
   and two new columns on `agent_state`.

2. **Deploy the Edge Function** — this is what lets the public dashboard
   safely change a risk profile without ever holding a write-capable key:
   - Supabase Dashboard → **Edge Functions** → **Deploy a new function** → **Via Editor**
   - Name it exactly `set-risk-profile`
   - Paste in the contents of `supabase/functions/set-risk-profile/index.ts`, click Deploy
   - Still on that function's page: **Manage** → **Secrets**, add:
     - `SUPABASE_URL` — your project URL
     - `SUPABASE_SERVICE_ROLE_KEY` — the same service role key from GitHub Secrets

3. **Run `backtest_stats.py` once manually** so the historical-range panel
   has something to show immediately, instead of waiting for Sunday:
   repo → Actions → "Backtest Stats" → Run workflow.

Nothing else changes — same GitHub Secrets, same dashboard URL, same
30-minute schedule for the actual trading.

## The built-in safety rails

- **Three separate switches gate real money** — `PAPER_TRADING`,
  `LIVE_SANDBOX`, and the `CONFIRM_LIVE_TRADING` secret all have to
  deliberately agree before a real order can go out (see `broker.py`'s
  `build_live_broker`). Flipping one by accident isn't enough.
- **A hard dollar ceiling per live order** (`MAX_LIVE_ORDER_USD`) on top of
  the percentage-based risk sizing.

- **Per-agent daily circuit breaker** (`max_daily_loss_pct`, default 8%) —
  if an agent's equity drops more than that in one UTC day, it auto-pauses
  itself until the next day and the pause shows up on the dashboard.
- **Stop-loss / take-profit** on every open position, persisted across runs
  so it still fires even if a scheduled run happens hours after entry.
- **`fail-fast: false`** in the workflow — one agent erroring on a bad API
  response doesn't take the other two down with it.
- **RLS on Supabase** — the anon key baked into `dashboard.html` is
  physically incapable of writing to your tables, only reading, so there's
  no way for the public dashboard to corrupt the bot's state even by accident.

## Extending it

- **More agents:** add an `AgentConfig` in `config.py` + its name in the
  workflow's `matrix.agent` list.
- **Different asset classes:** stocks (Alpaca, Interactive Brokers) or
  forex (OANDA) need their own data-feed/broker adapters, but can reuse
  the same `generate_signal(df)` / `execute(...)` interfaces.
- **Alerts:** a Discord or Telegram webhook call at the end of `main.py`
  (on a circuit-breaker trip, or on any error) means silence between
  check-ins actually means "fine," not "broken and nobody noticed."
