"""
Persists each agent's state (cash, positions, pause status) and trade
history to Supabase — this is what lets a run that starts on a brand-new,
empty GitHub Actions machine pick up exactly where the last run left off.

Needs two environment variables:
  SUPABASE_URL   — your project URL
  SUPABASE_KEY   — the SERVICE ROLE key (not the anon key!)

The service role key can write and bypasses row-level security — it must
only ever live in GitHub Secrets (or your local .env, gitignored), never
in a committed file and never in dashboard.html. dashboard.html uses the
separate, public-safe anon key, which — per supabase_schema.sql — can only
read, never write. Mixing these two up is the one mistake that actually
matters here, so if you're ever unsure which key you're holding, stop and
check the Supabase project settings before pasting it anywhere.

Note on agent_settings (risk profile): this module only READS it
(get_risk_profile). It never writes it — the only writer is the
set-risk-profile Edge Function, which runs server-side inside Supabase
with its own service role key, triggered by the dashboard. Keeping the
write path there (not here) means changing a risk profile doesn't need a
GitHub Actions run or a code deploy — it's live within a tick or two.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Optional

from supabase import create_client, Client


class SupabaseStateStore:
    def __init__(self):
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        self.client: Client = create_client(url, key)

    def load_state(self, agent_name: str) -> Optional[Dict]:
        res = self.client.table("agent_state").select("*").eq("agent_name", agent_name).execute()
        return res.data[0] if res.data else None

    def save_state(self, agent_name: str, cash: float, positions: Dict[str, float],
                    entry_prices: Dict[str, float], paused: bool, day: str, day_start_equity: float,
                    market_snapshot: Optional[Dict] = None, market_note: Optional[str] = None):
        payload = {
            "agent_name": agent_name,
            "cash": cash,
            "positions": json.dumps(positions),
            "entry_prices": json.dumps(entry_prices),
            "paused": paused,
            "day": day,
            "day_start_equity": day_start_equity,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if market_snapshot is not None:
            payload["market_snapshot"] = json.dumps(market_snapshot)
        if market_note is not None:
            payload["market_note"] = market_note
        self.client.table("agent_state").upsert(payload, on_conflict="agent_name").execute()

    def get_risk_profile(self, agent_name: str) -> str:
        """Reads the agent's current risk profile, defaulting to 'balanced'
        if nothing's been set (e.g. table just created, or dashboard never
        used to change it)."""
        res = self.client.table("agent_settings").select("risk_profile").eq("agent_name", agent_name).execute()
        if res.data:
            return res.data[0]["risk_profile"]
        return "balanced"

    def save_backtest_stats(self, agent_name: str, min_return_pct: float, max_return_pct: float,
                             median_return_pct: float, num_windows: int, window_days: int):
        self.client.table("backtest_stats").upsert({
            "agent_name": agent_name,
            "min_return_pct": min_return_pct,
            "max_return_pct": max_return_pct,
            "median_return_pct": median_return_pct,
            "num_windows": num_windows,
            "window_days": window_days,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="agent_name").execute()

    def log_trade(self, agent_name: str, symbol: str, side: str, qty: float,
                   price: float, fee: float, cash_after: float):
        self.client.table("trades").insert({
            "agent_name": agent_name,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": price,
            "fee": fee,
            "cash_after": cash_after,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }).execute()

    # --- Nightly refine: per-agent strategy parameter overrides ---
    # Written only by nightly_review.py (service role key, GitHub Actions),
    # read by main.py every tick. See strategy_params.py for the bounds every
    # override is checked against before use.

    def get_strategy_override(self, agent_name: str) -> Optional[Dict]:
        """None if there's no override OR the table doesn't exist yet — the
        agent then just trades its config.py defaults, same as before."""
        try:
            res = self.client.table("agent_overrides").select("*").eq("agent_name", agent_name).execute()
        except Exception as e:
            print(f"[{agent_name}] strategy override unavailable ({e}) — using config defaults")
            return None
        if not res.data:
            return None
        row = res.data[0]
        params = row.get("params")
        if isinstance(params, str):
            params = json.loads(params)
        return {**row, "params": params}

    def save_strategy_override(self, agent_name: str, family: str, params: Dict,
                               previous_params: Optional[Dict], reason: str, metrics: Dict):
        self.client.table("agent_overrides").upsert({
            "agent_name": agent_name,
            "family": family,
            "params": params,
            "previous_params": previous_params,
            "reason": reason,
            "metrics": metrics,
            "applied_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="agent_name").execute()

    def trades_since(self, iso_ts: str):
        res = self.client.table("trades").select("*").gte("timestamp", iso_ts).order("timestamp").execute()
        return res.data or []

    def all_agent_state(self):
        res = self.client.table("agent_state").select("*").execute()
        return res.data or []
