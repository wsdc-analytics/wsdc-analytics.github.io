-- Fix grants after security hardening:
-- table-level SELECT/INSERT for hub reads+writes; hide author_email via column REVOKE.
-- PostgREST needs table SELECT; column-only grants caused "permission denied for table".

GRANT SELECT, INSERT ON TABLE public.qa_boards TO anon, authenticated;
GRANT SELECT, INSERT ON TABLE public.qa_threads TO anon, authenticated;
GRANT SELECT, INSERT ON TABLE public.qa_posts TO anon, authenticated;

REVOKE UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLE public.qa_threads FROM anon, authenticated;
REVOKE UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLE public.qa_posts FROM anon, authenticated;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLE public.qa_boards FROM anon, authenticated;
GRANT SELECT ON TABLE public.qa_boards TO anon, authenticated;

REVOKE SELECT (author_email) ON TABLE public.qa_threads FROM anon, authenticated;
REVOKE SELECT (author_email) ON TABLE public.qa_posts FROM anon, authenticated;

GRANT INSERT (author_email) ON TABLE public.qa_threads TO anon, authenticated;
GRANT INSERT (author_email) ON TABLE public.qa_posts TO anon, authenticated;
