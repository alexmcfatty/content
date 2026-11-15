# Content Bank

Personal idea bank and script helper for short-form videos. One `index.html` PWA, ideas stored in Supabase.

- `index.html` — the whole app
- `rules.txt` — the script rules. Edit this any time; "Copy prompt" always uses the latest version.
- `config.js` — Supabase URL and anon key (blank = saves on this device only)
- `schema.sql` — run once in Supabase to create the `ideas` table
- `manifest.json`, `sw.js`, `icons/` — install to home screen

## Setup

### 1. Supabase (new free project)
1. Go to supabase.com, create a new project (any name, region Sydney).
2. SQL Editor → New query → paste all of `schema.sql` → Run.
3. Authentication → Email Templates → **Magic Link**: add this line to the email body so it includes a code:
   `Your code: {{ .Token }}`
   (The app signs in with the code, because on iPhone a tapped link opens Safari, not the home-screen app.)
4. Project Settings → API: copy the **Project URL** and the **anon public** key into `config.js`.

### 2. Hosting
Push this folder to its own GitHub repo and turn on Pages (Settings → Pages → Deploy from branch → `main` / root).
Then in Supabase → Authentication → URL Configuration, set the Site URL to the Pages address.

### 3. First sign-in, then lock it
1. Open the app, enter your email, type the code from the email.
2. Supabase → Authentication → Sign In / Providers → turn **off** "Allow new users to sign up". Now only your account can get in.

### 4. Install on your phone
- iPhone: open the site in Safari → Share → Add to Home Screen.
- Android: Chrome menu → Install app.

## Using it
- Save an idea: type it, hit Save. Tags are optional.
- Sunday: tap **Pick my week** → swap any → **Accept week**. Rules: 3 light + 1 serious, at least 2 Training in public, max 1 per series. If there aren't enough ideas it relaxes the series rule first and tells you.
- Script: open an idea → **Copy prompt** → **Open Claude** → paste. Tweak buttons copy a follow-up line for the same chat. Paste the final script back and **Save script** (moves Idea → Scripted).
- Tip: make a Claude Project with `rules.txt` as its instructions, and you only need to paste the idea part.
