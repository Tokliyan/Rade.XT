-- Run this once in your Supabase project's SQL editor (Database -> SQL Editor).
-- Safe to re-run: uses "if not exists" throughout.

create table if not exists agent_state (
  agent_name text primary key,
  cash numeric not null,
  positions jsonb not null default '{}',
  entry_prices jsonb not null default '{}',
  paused boolean not null default false,
  day date,
  day_start_equity numeric,
  updated_at timestamptz not null default now()
);

create table if not exists trades (
  id bigserial primary key,
  agent_name text not null,
  symbol text not null,
  side text not null,
  qty numeric not null,
  price numeric not null,
  fee numeric not null,
  cash_after numeric not null,
  timestamp timestamptz not null default now()
);

create index if not exists trades_agent_time_idx on trades (agent_name, timestamp desc);

-- Row-level security: the dashboard reads with the PUBLIC anon key, so it
-- must only ever be able to SELECT, never write. The bot writes using the
-- SERVICE ROLE key (set as SUPABASE_KEY in GitHub Secrets), which bypasses
-- RLS entirely — so these policies only govern what the anon/public key,
-- and therefore the dashboard, can do.

alter table agent_state enable row level security;
alter table trades enable row level security;

drop policy if exists "public read agent_state" on agent_state;
create policy "public read agent_state" on agent_state for select using (true);

drop policy if exists "public read trades" on trades;
create policy "public read trades" on trades for select using (true);

-- No insert/update/delete policies are created for the anon role, so the
-- public dashboard key literally cannot write to these tables, even by
-- mistake.

-- v2 additions: market snapshot on agent_state, switchable risk profiles,
-- and honest historical-range stats (not a forecast — see backtest_stats.py)

alter table agent_state add column if not exists market_snapshot jsonb not null default '{}';
alter table agent_state add column if not exists market_note text;

create table if not exists agent_settings (
  agent_name text primary key,
  risk_profile text not null default 'balanced' check (risk_profile in ('conservative','balanced','aggressive')),
  updated_at timestamptz not null default now()
);
alter table agent_settings enable row level security;
drop policy if exists "public read agent_settings" on agent_settings;
create policy "public read agent_settings" on agent_settings for select using (true);
-- Deliberately no write policy for anon here either. The ONLY way this
-- table gets written to is the set-risk-profile Edge Function, which
-- authenticates with the service role key server-side — never from the
-- browser. See supabase/functions/set-risk-profile/index.ts.

create table if not exists backtest_stats (
  agent_name text primary key,
  min_return_pct numeric,
  max_return_pct numeric,
  median_return_pct numeric,
  num_windows integer,
  window_days integer,
  updated_at timestamptz not null default now()
);
alter table backtest_stats enable row level security;
drop policy if exists "public read backtest_stats" on backtest_stats;
create policy "public read backtest_stats" on backtest_stats for select using (true);
