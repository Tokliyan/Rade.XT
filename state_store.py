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
                    entry_prices: Dict[str, float], paused: bool, day: str, day_start_equity: float):
        self.client.table("agent_state").upsert({
            "agent_name": agent_name,
            "cash": cash,
            "positions": json.dumps(positions),
            "entry_prices": json.dumps(entry_prices),
            "paused": paused,
            "day": day,
            "day_start_equity": day_start_equity,
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
