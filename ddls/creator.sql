create table public.creator (
  id uuid primary key default gen_random_uuid(),
  nsfw boolean not null default false,
  niches text[] default '{}',
  persona text[] default '{}',
  emojis_enabled boolean not null default false,
  emojis_used text,
  image_url text,
  created_at timestamptz default now()
);