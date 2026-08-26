-- Q&A hub security hardening: hide emails from anon SELECT; https-only page_url

-- Column-level SELECT: anon/authenticated cannot read author_email
REVOKE SELECT ON TABLE public.qa_threads FROM anon, authenticated;
GRANT SELECT (
  id,
  board_id,
  title,
  author_name,
  page_url,
  body,
  is_hidden,
  is_pinned,
  created_at
) ON TABLE public.qa_threads TO anon, authenticated;

REVOKE SELECT ON TABLE public.qa_posts FROM anon, authenticated;
GRANT SELECT (
  id,
  thread_id,
  author_name,
  body,
  is_hidden,
  is_op,
  created_at
) ON TABLE public.qa_posts TO anon, authenticated;

-- INSERT still allowed (incl. author_email write); no public UPDATE/DELETE
GRANT INSERT ON TABLE public.qa_threads TO anon, authenticated;
GRANT INSERT ON TABLE public.qa_posts TO anon, authenticated;
GRANT SELECT ON TABLE public.qa_boards TO anon, authenticated;

-- https-only related links
ALTER TABLE public.qa_threads DROP CONSTRAINT IF EXISTS qa_threads_page_url_check;
ALTER TABLE public.qa_threads DROP CONSTRAINT IF EXISTS qa_threads_page_url_https_check;
ALTER TABLE public.qa_threads
  ADD CONSTRAINT qa_threads_page_url_https_check
  CHECK (
    page_url IS NULL
    OR (
      char_length(page_url) <= 500
      AND page_url ~* '^https://[^\s]+$'
    )
  );
