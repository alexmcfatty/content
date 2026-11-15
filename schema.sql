-- Run this once in Supabase: SQL Editor -> New query -> paste -> Run.

create table if not exists public.ideas (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null default auth.uid() references auth.users(id) on delete cascade,
  text        text not null,
  pillar      text,
  tone        text check (tone in ('Light','Serious')),
  series      text,
  status      text not null default 'Idea' check (status in ('Idea','Scripted','Filmed','Posted')),
  script      text,
  week_of     date,          -- Monday of the week it was picked for
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

alter table public.ideas enable row level security;

-- Only the signed-in owner can see or change their ideas.
drop policy if exists "own ideas" on public.ideas;
create policy "own ideas" on public.ideas
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

create or replace function public.touch_updated_at() returns trigger
language plpgsql as $$ begin new.updated_at = now(); return new; end $$;

drop trigger if exists ideas_touch on public.ideas;
create trigger ideas_touch before update on public.ideas
  for each row execute function public.touch_updated_at();
