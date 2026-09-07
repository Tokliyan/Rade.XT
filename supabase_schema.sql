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
