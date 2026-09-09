# Supplier Bill Management System — Cloud Deployment Guide

This app has been converted from a local-only setup (SQLite file +
local Tesseract + local Ollama) to a fully cloud-hosted, free setup:

| Piece                | Was                          | Now                                   |
|-----------------------|-------------------------------|----------------------------------------|
| Hosting               | `streamlit run` on your PC   | **Streamlit Community Cloud** (free)  |
| Database              | local `data/database.db`     | **Supabase Postgres** (free tier)     |
| Invoice photo storage | local `uploads/` folder      | **Supabase Storage** (free tier)      |
| AI extraction         | local Ollama (`llama3.2:3b`) | **Google Gemini** `gemini-2.0-flash` (free tier) |
| OCR                   | local Tesseract .exe         | Tesseract installed via `packages.txt`|

Nothing here costs money at normal small-business volume. All four
services (Streamlit Cloud, Supabase, Gemini) have generous free tiers.

---

## 1. Create your Supabase project (database + photo storage)

1. Go to https://supabase.com → sign up free → **New project**.
2. Pick a name, a strong database password (save it), and a region
   close to your users. Wait ~2 minutes for it to provision.
3. **Database connection details:** Project → *Connect* (top of
   dashboard) → note the **Host**, **Port**, **Database**, **User**,
   and use the password you set. You'll paste these into Streamlit
   secrets in step 4.
4. **API keys:** Project Settings → *API* → note the **Project URL**
   and the **`service_role` secret key** (not the `anon` key — the
   service role key is required so the app can upload photos).
5. **Create the storage bucket for invoice photos:**
   Storage (left sidebar) → *New bucket* → name it exactly
   `invoice-photos` → make it **Public** (so `st.image()` can display
   photos directly by URL) → Create.
6. **Create the database tables:** you'll run this once from your
   own computer after setting up secrets (step 3 below) — see
   step 5 further down.

## 2. Get a free Google Gemini API key

1. Go to https://aistudio.google.com/apikey.
2. Sign in, click **Create API key**, copy it.
3. The free tier is generous enough for normal invoice-processing
   volume; if you ever outgrow it, Gemini simply returns a quota
   error and the app falls back to an empty form the staff member
   can fill in manually.

## 3. Configure secrets

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
and fill in the real values from steps 1–2. **Never commit this
file** — `.gitignore` already excludes it.

For Streamlit Community Cloud (step 6), you'll paste the same
key/value pairs into the app's **Secrets** settings in the web UI
instead of uploading this file.

## 4. Install dependencies locally (optional, for testing)

```bash
pip install -r requirements.txt
```

You'll also need the Tesseract binary installed locally (Windows
users: same installer as before; on Mac: `brew install tesseract`;
on Linux: `sudo apt install tesseract-ocr`).

## 5. Create the database tables (run once)

With your `.streamlit/secrets.toml` filled in:

```bash
python database.py
```

This connects to Supabase and creates all five tables (`users`,
`suppliers`, `invoices`, `invoice_items`, `payments`,
`expected_invoices`). Then create your first login:

```bash
python create_user.py
```

## 6. Push to GitHub

Create a new GitHub repository and push this project to it
(everything except `.streamlit/secrets.toml`, which is gitignored).

```bash
git init
git add .
git commit -m "Cloud-ready supplier bill system"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

## 7. Deploy on Streamlit Community Cloud

1. Go to https://share.streamlit.io → sign in with GitHub → **New app**.
2. Pick your repository, branch `main`, and main file `app.py`.
3. Before clicking Deploy, open **Advanced settings → Secrets** and
   paste in the full contents of your `secrets.toml` (same keys as
   `.streamlit/secrets.toml.example`, real values).
4. Click **Deploy**. Streamlit Cloud will:
   - install `packages.txt` (Tesseract) via apt,
   - install `requirements.txt` via pip,
   - start the app.
5. You'll get a public URL like
   `https://your-app-name.streamlit.app` — this is now accessible
   from anywhere, on any device, for free.

## 8. Day-to-day use

- Share the `streamlit.app` URL with your staff/boss — no VPN, no
  installer, works on phones too.
- To add more users later, run `python create_user.py` locally
  (pointed at the same Supabase secrets) — there's no in-app "add
  user" screen yet.
- The free tiers: Streamlit Cloud apps sleep after inactivity and
  wake on the next visit (a few seconds' delay); Supabase free
  projects pause after 7 days with zero traffic (a dashboard click
  wakes it back up); Gemini free tier resets daily. All fine for a
  small internal tool.

## What changed in the code

- `database.py` — now connects to Postgres (`psycopg2`) instead of
  SQLite, but a small compatibility wrapper means every existing
  `connection.execute(sql, params).fetchone()/.fetchall()` call and
  `row["column"]` access in `app.py` and `auth.py` kept working
  unchanged.
- `storage.py` — new module; uploads invoice photos to Supabase
  Storage and returns a public URL, used in place of writing to a
  local `uploads/` folder.
- `ai_extractor.py` — `extract_invoice()` now calls the Gemini API
  with the same JSON schema you already had, instead of a local
  Ollama server (which can't run on free cloud hosting).
- `ocr.py` — dropped the hardcoded Windows Tesseract path;
  `packages.txt` installs Tesseract system-wide on Streamlit Cloud.
- `app.py` — invoice photo save/display now goes through
  `storage.py` instead of the local filesystem; two `INSERT`
  statements gained a `RETURNING` clause since Postgres has no
  `cursor.lastrowid`; invoice/supplier search uses `ILIKE` instead
  of `LIKE` to keep the same case-insensitive search behavior
  SQLite had by default.
