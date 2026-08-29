-- Article thumbs (up/down) — replaces Lyket / GitHub reactions.json flow.
-- Votes are per voter_key; baseline holds migrated legacy counts.

create table if not exists public.article_reaction_votes (
  article_id text not null,
  voter_key text not null,
  value text not null check (value in ('up', 'down')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (article_id, voter_key)
);

create table if not exists public.article_reaction_baseline (
  article_id text primary key,
  up_count integer not null default 0 check (up_count >= 0),
  down_count integer not null default 0 check (down_count >= 0)
);

create index if not exists article_reaction_votes_article_idx
  on public.article_reaction_votes (article_id);

alter table public.article_reaction_votes enable row level security;
alter table public.article_reaction_baseline enable row level security;

-- Public read of aggregates via API (service role). No anon policies needed for direct table access.
revoke all on table public.article_reaction_votes from anon, authenticated, public;
revoke all on table public.article_reaction_baseline from anon, authenticated, public;

-- Seed baseline from legacy reactions.json mapping (positive→up, negative→down, neutral dropped).
insert into public.article_reaction_baseline (article_id, up_count, down_count) values
  ('article_secondary_role_ru', 1, 0),
  ('overview_2025_ru', 1, 0),
  ('rules_evolution_2025_en', 1, 0),
  ('rules_evolution_2025_es', 1, 0),
  ('rules_evolution_2025_ru', 11, 1),
  ('article_3year_rule_ru', 9, 0),
  ('article_division_transition_ru', 5, 0)
on conflict (article_id) do update set
  up_count = excluded.up_count,
  down_count = excluded.down_count;
