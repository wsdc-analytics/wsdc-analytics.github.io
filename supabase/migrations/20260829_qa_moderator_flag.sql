-- Soft-highlight staff/moderator authors in Q&A
alter table public.qa_posts
  add column if not exists is_moderator boolean not null default false;

alter table public.qa_threads
  add column if not exists is_moderator boolean not null default false;

-- Anon clients must not self-claim moderator
drop policy if exists qa_posts_insert on public.qa_posts;
create policy qa_posts_insert on public.qa_posts
  for insert to anon, authenticated
  with check (
    is_hidden = false
    and is_moderator = false
    and char_length(trim(author_name)) >= 1
    and char_length(trim(body)) >= 1
    and exists (
      select 1 from public.qa_threads t
      where t.id = thread_id and t.is_hidden = false
    )
  );

drop policy if exists qa_threads_insert on public.qa_threads;
create policy qa_threads_insert on public.qa_threads
  for insert to anon, authenticated
  with check (
    is_hidden = false
    and is_pinned = false
    and is_moderator = false
    and char_length(trim(title)) >= 3
    and char_length(trim(author_name)) >= 1
    and char_length(trim(body)) >= 3
  );
