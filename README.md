# FindIt — Lost & Found (Python + Streamlit + Supabase)

FindIt is a beginner-friendly multi-user web app for reporting lost/found items, uploading photos, searching listings, suggesting potential matches, and sending claim requests.

## Files
- `app.py` — Streamlit application
- `requirements.txt` — Python dependencies
- `supabase_setup.sql` — core database tables, access policies, and image storage bucket
- `supabase_messaging_setup.sql` — usernames, private messages, and Realtime chat
- `supabase_features_setup.sql` — saves, notifications, search alerts, map coordinates, private verification, blocks and reports
- `findit_features.py` — additional matching, QR, map, profile and safety UI
- `.streamlit/secrets.toml.example` — configuration template

## 1. Create the Supabase backend
1. Create a project at https://supabase.com/.
2. Open **Project Settings → API** (or the API Keys section in the current dashboard).
3. Copy the Project URL and the **publishable/anon client key**. Never use a `service_role` or secret key in Streamlit.
4. Open **SQL Editor → New query**, paste all of `supabase_setup.sql`, and run it.
5. Confirm the `listings` and `claims` tables exist in Table Editor and the `findit-images` bucket exists in Storage.

### Authentication note
For a real deployment, enable email confirmation in Supabase Auth. New users may need to click the email confirmation link before logging in. Configure the site's allowed redirect URLs in Supabase Auth settings for your deployed app.

## 2. Enable messaging and advanced FindIt features

After the core setup is complete, run these files in Supabase **SQL Editor**, in this order:

1. `supabase_messaging_setup.sql` — usernames, conversations, messages and live chat.
2. `supabase_features_setup.sql` — saved listings, notifications, saved searches, owner-only verification details, blocks/reports and optional approximate coordinates.

Both migrations are designed to be rerunnable and additive. They do not delete existing listings, claims, accounts or messages.

The expanded app includes:
- Rule-based lost/found matching and duplicate-report warnings.
- Saved listings and saved-search notifications.
- A notification inbox for messages, claims, saved-search matches and saved-listing changes.
- Map discovery using optional approximate coordinates.
- Private ownership-check details that only the listing owner can read.
- Community profiles, contribution badges and a username directory.
- QR codes for sharing individual listings.
- Report/block controls, with a safety-report queue in the admin panel.

**QR code setup:** The app tries to detect its own URL. For the most reliable QR links, add your deployed Streamlit URL to Cloud secrets:

```toml
[app]
base_url = "https://YOUR-FINDIT-APP-URL"
```

Use an approximate public landmark when entering map coordinates. Do not publish home addresses or sensitive item details.

## 3. Run locally
Install Python 3.10 or newer. In the project folder:

```bash
python -m venv .venv
```

Windows:
```powershell
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install packages:
```bash
pip install -r requirements.txt
```

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and replace the placeholder values with your Supabase project URL and publishable/anon key.

Run:
```bash
streamlit run app.py
```

## 4. Deploy online
1. Create a private or public GitHub repository and upload the project files. Do not commit `.streamlit/secrets.toml`.
2. Go to https://share.streamlit.io/ and deploy the repository, choosing `app.py` as the main file.
3. In Streamlit Cloud app settings, add these secrets:

```toml
[supabase]
url = "https://YOUR-PROJECT.supabase.co"
anon_key = "YOUR-SUPABASE-PUBLISHABLE-OR-ANON-KEY"
```

4. Deploy/reboot the app and test signup/login from two different accounts/devices.

## 5. Important project limitations / safety
- The starter has account login, listings, image uploads, search, basic keyword matching, claim requests, and owner status updates.
- It is a college-project starter, not a fully audited production service. Test permissions carefully before public use.
- The `findit-images` bucket is public so photos can display easily. Anyone with a photo URL can view it; upload only non-sensitive item photos.
- Claim messages are private to the claimant and listing owner through row-level security. This version does not expose users' email addresses or provide in-app direct messaging.
- Potential matches are rule-based suggestions, not AI and not proof of ownership.
- Admin moderation is not included in this starter; add it with a separate role-controlled policy before real public launch.
- Configure Supabase Auth rate limits, email confirmation, and site URL/redirects before sharing widely.
