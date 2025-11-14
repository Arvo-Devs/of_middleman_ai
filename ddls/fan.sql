create table public.fan (
  id uuid primary key default gen_random_uuid(),
  lifetime_spend varchar,
  created_at timestamptz default now()
);