/**
 * Public Q&A hub config (anon key is publishable by design).
 * Set apiBase to your Vercel deployment for mod/notify endpoints.
 * Leave apiBase empty to disable Telegram notify + server moderation until configured.
 */
window.QA_CONFIG = {
  supabaseUrl: "https://tougqwxmahkwnaculiju.supabase.co",
  supabaseAnonKey:
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRvdWdxd3htYWhrd25hY3VsaWp1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUyMjcyNzMsImV4cCI6MjA5MDgwMzI3M30.0sDagftyoM21lkV2sZJf5jhvtHR3GUE9IX10lznAOCw",
  /* Same host pattern as REACTIONS_API when deployed */
  apiBase: "https://wsdc-analytics-repo.vercel.app",
};
