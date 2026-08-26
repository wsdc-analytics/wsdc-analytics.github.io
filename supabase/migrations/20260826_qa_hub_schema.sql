-- Q&A Community Hub schema (isolated qa_* tables)
-- Applied to project tougqwxmahkwnaculiju (shared org project; qa_* prefix)

create table if not exists public.qa_boards (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  title text not null,
  sort_order int not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists public.qa_threads (
  id uuid primary key default gen_random_uuid(),
  board_id uuid not null references public.qa_boards(id) on delete cascade,
  title text not null check (char_length(title) between 3 and 160),
  author_name text not null check (char_length(author_name) between 1 and 80),
  author_email text null check (author_email is null or author_email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  page_url text null check (page_url is null or char_length(page_url) <= 500),
  body text not null check (char_length(body) between 3 and 8000),
  is_hidden boolean not null default false,
  is_pinned boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.qa_posts (
  id uuid primary key default gen_random_uuid(),
  thread_id uuid not null references public.qa_threads(id) on delete cascade,
  author_name text not null check (char_length(author_name) between 1 and 80),
  author_email text null check (author_email is null or author_email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  body text not null check (char_length(body) between 1 and 8000),
  is_hidden boolean not null default false,
  is_op boolean not null default false,
  created_at timestamptz not null default now()
);

create index if not exists qa_threads_board_created_idx
  on public.qa_threads (board_id, is_pinned desc, created_at desc);
create index if not exists qa_posts_thread_created_idx
  on public.qa_posts (thread_id, created_at asc);

alter table public.qa_boards enable row level security;
alter table public.qa_threads enable row level security;
alter table public.qa_posts enable row level security;

drop policy if exists qa_boards_select on public.qa_boards;
create policy qa_boards_select on public.qa_boards
  for select to anon, authenticated using (true);

drop policy if exists qa_threads_select on public.qa_threads;
create policy qa_threads_select on public.qa_threads
  for select to anon, authenticated using (is_hidden = false);

drop policy if exists qa_threads_insert on public.qa_threads;
create policy qa_threads_insert on public.qa_threads
  for insert to anon, authenticated
  with check (
    is_hidden = false
    and is_pinned = false
    and char_length(trim(title)) >= 3
    and char_length(trim(author_name)) >= 1
    and char_length(trim(body)) >= 3
  );

drop policy if exists qa_posts_select on public.qa_posts;
create policy qa_posts_select on public.qa_posts
  for select to anon, authenticated using (is_hidden = false);

drop policy if exists qa_posts_insert on public.qa_posts;
create policy qa_posts_insert on public.qa_posts
  for insert to anon, authenticated
  with check (
    is_hidden = false
    and char_length(trim(author_name)) >= 1
    and char_length(trim(body)) >= 1
    and exists (
      select 1 from public.qa_threads t
      where t.id = thread_id and t.is_hidden = false
    )
  );

insert into public.qa_boards (slug, title, sort_order) values
  ('articles', 'Articles', 10),
  ('dashboards', 'Dashboards', 20),
  ('summary-points', 'Summary Points', 30),
  ('new-champions', 'New Champions', 40),
  ('calendar', 'Calendar', 50),
  ('other', 'Other', 60)
on conflict (slug) do update set title = excluded.title, sort_order = excluded.sort_order;
