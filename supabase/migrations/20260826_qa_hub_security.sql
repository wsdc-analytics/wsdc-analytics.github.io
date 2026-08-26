-- Q&A hub security hardening: https-only page_url + hide author_email from anon SELECT
-- NOTE: Prefer table-level SELECT + REVOKE SELECT (author_email).
-- Column-only GRANT SELECT after REVOKE SELECT ON TABLE breaks PostgREST
-- ("permission denied for table"). See 20260826_qa_hub_fix_grants.sql.

GRANT SELECT, INSERT ON TABLE public.qa_threads TO anon, authenticated;
GRANT SELECT, INSERT ON TABLE public.qa_posts TO anon, authenticated;
GRANT SELECT ON TABLE public.qa_boards TO anon, authenticated;

REVOKE UPDATE, DELETE ON TABLE public.qa_threads FROM anon, authenticated;
REVOKE UPDATE, DELETE ON TABLE public.qa_posts FROM anon, authenticated;

REVOKE SELECT (author_email) ON TABLE public.qa_threads FROM anon, authenticated;
REVOKE SELECT (author_email) ON TABLE public.qa_posts FROM anon, authenticated;
GRANT INSERT (author_email) ON TABLE public.qa_threads TO anon, authenticated;
GRANT INSERT (author_email) ON TABLE public.qa_posts TO anon, authenticated;

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
