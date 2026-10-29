import os
from datetime import date
from io import BytesIO

import streamlit as st
from PIL import Image
from supabase import create_client, Client

st.set_page_config(page_title="FindIt | Lost & Found", page_icon="🔎", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px;}
.hero {padding: 1.5rem 1.7rem; border-radius: 18px; background: linear-gradient(120deg,#102a43,#2463a6); color: white; margin-bottom: 1.2rem;}
.hero h1 {color:white; margin:0; font-size:2.5rem;}
.hero p {color:#e5efff; margin:.35rem 0 0 0;}
.small-muted {color: #667085; font-size: .9rem;}
.item-card {border: 1px solid #e5e7eb; border-radius: 14px; padding: 12px; margin-bottom: 12px;}
</style>
""", unsafe_allow_html=True)


def get_setting(section, key, env_name=None):
    try:
        value = st.secrets[section][key]
        if value:
            return value
    except Exception:
        pass
    return os.getenv(env_name or key.upper())


def supabase_client():
    # Keep the authenticated Supabase client per Streamlit browser session.
    # A globally cached client could mix authentication state between users.
    if st.session_state.get("_supabase_client") is not None:
        return st.session_state["_supabase_client"]
    url = get_setting("supabase", "url", "SUPABASE_URL")
    key = get_setting("supabase", "anon_key", "SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    client = create_client(url, key)
    st.session_state["_supabase_client"] = client
    return client


def friendly_error(exc):
    message = str(exc)
    if "Invalid login credentials" in message:
        return "Email or password is incorrect."
    if "Email not confirmed" in message:
        return "Please confirm your email using the link sent by Supabase, then log in."
    if "row-level security" in message.lower() or "permission denied" in message.lower():
        return "Permission was denied. Check that you ran the SQL setup and enabled the required policies."
    return message[:400]


def get_user():
    return st.session_state.get("user")


def do_logout():
    st.session_state.pop("user", None)
    st.session_state.pop("page", None)
    st.rerun()


def upload_image(client: Client, uploaded_file, user_id: str):
    if uploaded_file is None:
        return None
    image = Image.open(uploaded_file).convert("RGB")
    image.thumbnail((1400, 1400))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85, optimize=True)
    path = f"{user_id}/{os.urandom(8).hex()}.jpg"
    client.storage.from_("findit-images").upload(
        path,
        buffer.getvalue(),
        file_options={"content-type": "image/jpeg", "upsert": "false"},
    )
    return client.storage.from_("findit-images").get_public_url(path)


def fetch_listings(client: Client):
    result = client.table("listings").select("*").order("created_at", desc=True).execute()
    return result.data or []


def fetch_claims(client: Client):
    result = client.table("claims").select("*").order("created_at", desc=True).execute()
    return result.data or []


def render_listing_card(item, show_claim_button=False, client=None, user=None):
    with st.container(border=True):
        left, right = st.columns([1, 2.2], gap="medium")
        with left:
            if item.get("image_url"):
                st.image(item["image_url"], use_container_width=True)
            else:
                st.markdown("### 📦\n_No photo uploaded_")
        with right:
            kind = "🔴 LOST" if item.get("listing_type") == "lost" else "🟢 FOUND"
            st.markdown(f"**{kind}** · `{item.get('status', 'open').upper()}`")
            st.subheader(item.get("title", "Untitled item"))
            st.write(item.get("description", "No description provided."))
            st.caption(
                f"Category: {item.get('category', 'Other')}  ·  "
                f"Colour: {item.get('color') or 'Not specified'}"
            )
            st.caption(
                f"Location: {item.get('location', 'Not specified')}  ·  "
                f"Date: {item.get('event_date') or 'Not specified'}"
            )
            st.caption(f"Listing ID: {item.get('id', '')}")
            if show_claim_button and client and user and item.get("owner_id") != user["id"] and item.get("status") == "open":
                with st.form(f"claim_{item['id']}"):
                    message = st.text_area(
                        "Claim message",
                        placeholder="Describe a detail that helps verify this is your item. Avoid sharing sensitive information.",
                        key=f"claim_message_{item['id']}",
                    )
                    submitted = st.form_submit_button("Request to connect")
                    if submitted:
                        try:
                            client.table("claims").insert({
                                "listing_id": item["id"],
                                "claimant_id": user["id"],
                                "message": message.strip() or "I'd like to discuss this item.",
                            }).execute()
                            st.success("Request sent to the listing owner.")
                            st.rerun()
                        except Exception as exc:
                            st.error(friendly_error(exc))


def main():
    client = supabase_client()
    st.markdown("""
    <div class="hero">
      <h1>🔎 FindIt</h1>
      <p>Lost something? Found something? Let’s help it find its way home.</p>
    </div>
    """, unsafe_allow_html=True)

    if client is None:
        st.error("FindIt is not configured yet. Add your Supabase URL and anon key to `.streamlit/secrets.toml`.")
        st.code('[supabase]\nurl = "https://YOUR-PROJECT.supabase.co"\nanon_key = "YOUR-SUPABASE-ANON-KEY"', language="toml")
        st.info("Follow README.md and run supabase_setup.sql in your Supabase project's SQL Editor.")
        st.stop()

    user = get_user()
    if not user:
        login_tab, signup_tab = st.tabs(["Log in", "Create account"])
        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email").strip().lower()
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)
                if submitted:
                    try:
                        response = client.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = {
                            "id": response.user.id,
                            "email": response.user.email,
                        }
                        st.rerun()
                    except Exception as exc:
                        st.error(friendly_error(exc))
        with signup_tab:
            st.write("Create an account to post listings and contact other users.")
            with st.form("signup_form"):
                new_email = st.text_input("Email address", key="signup_email").strip().lower()
                new_password = st.text_input("Password (at least 8 characters)", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm password", type="password")
                submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
                if submitted:
                    if not new_email or "@" not in new_email:
                        st.error("Enter a valid email address.")
                    elif len(new_password) < 8:
                        st.error("Use a password with at least 8 characters.")
                    elif new_password != confirm_password:
                        st.error("The passwords do not match.")
                    else:
                        try:
                            response = client.auth.sign_up({"email": new_email, "password": new_password})
                            if response.session:
                                st.session_state.user = {
                                    "id": response.user.id,
                                    "email": response.user.email,
                                }
                                st.success("Account created.")
                                st.rerun()
                            else:
                                st.success("Account created. Check your email for the confirmation link, then log in.")
                        except Exception as exc:
                            st.error(f"Error type: {type(exc).__name__}")
                            st.code(str(exc))
        st.caption("For safety, use a unique password. FindIt never asks for your email password anywhere except Supabase authentication.")
        st.stop()

    with st.sidebar:
        st.markdown("## FindIt")
        st.caption(user.get("email", "Signed in"))
        page = st.radio(
            "Navigation",
            ["Home & Search", "Report an item", "My dashboard", "Claims inbox"],
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("Never post full addresses, ID numbers, or private details in public descriptions.")
        if st.button("Log out", use_container_width=True):
            do_logout()

    try:
        listings = fetch_listings(client)
    except Exception as exc:
        st.error("Couldn't load listings. " + friendly_error(exc))
        st.stop()

    if page == "Home & Search":
        st.title("Find an item")
        st.write("Search public listings and filter down to likely matches.")
        qcol, typecol, catcol = st.columns([2, 1, 1])
        with qcol:
            query = st.text_input("Search keywords", placeholder="e.g. black wallet, blue bottle, library")
        with typecol:
            type_filter = st.selectbox("Listing type", ["All", "Lost", "Found"])
        with catcol:
            categories = ["All"] + sorted(set(x.get("category", "Other") for x in listings))
            category_filter = st.selectbox("Category", categories)
        location_filter = st.text_input("Location contains", placeholder="e.g. campus, library, bus stop")
        open_only = st.checkbox("Show only unresolved listings", value=True)

        filtered = []
        q = query.lower().strip()
        loc = location_filter.lower().strip()
        for item in listings:
            searchable = " ".join(str(item.get(k) or "") for k in ["title", "description", "category", "color", "location"]).lower()
            if q and q not in searchable:
                continue
            if type_filter != "All" and item.get("listing_type") != type_filter.lower():
                continue
            if category_filter != "All" and item.get("category") != category_filter:
                continue
            if loc and loc not in str(item.get("location", "")).lower():
                continue
            if open_only and item.get("status") != "open":
                continue
            filtered.append(item)

        st.caption(f"{len(filtered)} listing(s) found")
        if not filtered:
            st.info("No matching listings yet. Try a broader search or report the item.")
        for item in filtered:
            render_listing_card(item, show_claim_button=True, client=client, user=user)

        st.divider()
        st.subheader("Potential matches")
        st.caption("FindIt compares the keywords, category, colour and location of open lost/found reports. These are suggestions, not proof of ownership.")
        open_lost = [x for x in listings if x.get("listing_type") == "lost" and x.get("status") == "open" and x.get("owner_id") != user["id"]]
        open_found = [x for x in listings if x.get("listing_type") == "found" and x.get("status") == "open" and x.get("owner_id") != user["id"]]
        matches = []
        for lost in open_lost:
            for found in open_found:
                score = 0
                if lost.get("category") and lost.get("category") == found.get("category"):
                    score += 3
                if lost.get("color") and found.get("color") and lost["color"].lower() == found["color"].lower():
                    score += 2
                lost_words = set((lost.get("title", "") + " " + lost.get("description", "")).lower().split())
                found_words = set((found.get("title", "") + " " + found.get("description", "")).lower().split())
                common = lost_words & found_words
                ignored = {"the", "a", "an", "and", "or", "with", "my", "is", "it", "of", "to", "in"}
                score += min(4, len(common - ignored))
                if lost.get("location") and found.get("location") and lost["location"].lower() == found["location"].lower():
                    score += 1
                if score >= 3:
                    matches.append((score, lost, found))
        matches.sort(key=lambda x: x[0], reverse=True)
        if not matches:
            st.write("No strong matches found yet.")
        for score, lost, found in matches[:5]:
            with st.expander(f"Possible match (score {score}) · {lost['title']} ↔ {found['title']}"):
                a, b = st.columns(2)
                with a:
                    st.markdown("**Lost report**")
                    render_listing_card(lost)
                with b:
                    st.markdown("**Found report**")
                    render_listing_card(found)

    elif page == "Report an item":
        st.title("Report an item")
        st.write("Share enough detail to identify the item, but keep one or two identifying details private so the owner can verify a claim.")
        with st.form("report_form", clear_on_submit=True):
            listing_type = st.radio("What are you reporting?", ["Lost item", "Found item"], horizontal=True)
            title = st.text_input("Item name", placeholder="e.g. Black wireless earbuds case")
            category = st.selectbox("Category", ["Electronics", "Wallet / Cards", "Keys", "Bag", "Clothing", "Books / Stationery", "Jewellery", "Bottle / Container", "Other"])
            color = st.text_input("Colour / visible characteristics", placeholder="e.g. matte black with a small blue sticker")
            description = st.text_area("Description", placeholder="Brand, size, distinctive marks, etc. Don't include sensitive numbers.")
            location = st.text_input("Where was it lost/found?", placeholder="e.g. Block B library, near the main gate")
            event_date = st.date_input("Date lost/found", value=date.today(), max_value=date.today())
            uploaded = st.file_uploader("Item photo (JPG, JPEG or PNG)", type=["jpg", "jpeg", "png"])
            submitted = st.form_submit_button("Publish listing", type="primary", use_container_width=True)
            if submitted:
                if len(title.strip()) < 2:
                    st.error("Enter an item name.")
                elif len(description.strip()) < 8:
                    st.error("Add a slightly more detailed description (at least 8 characters).")
                elif len(location.strip()) < 2:
                    st.error("Enter the place where it was lost or found.")
                else:
                    try:
                        image_url = upload_image(client, uploaded, user["id"]) if uploaded else None
                        payload = {
                            "owner_id": user["id"],
                            "listing_type": "lost" if listing_type == "Lost item" else "found",
                            "title": title.strip()[:100],
                            "category": category,
                            "color": color.strip()[:120],
                            "description": description.strip()[:1500],
                            "location": location.strip()[:200],
                            "event_date": event_date.isoformat(),
                            "image_url": image_url,
                            "status": "open",
                        }
                        client.table("listings").insert(payload).execute()
                        st.success("Your listing has been published!")
                        st.rerun()
                    except Exception as exc:
                        st.error("Could not publish the listing. " + friendly_error(exc))

    elif page == "My dashboard":
        st.title("My dashboard")
        mine = [x for x in listings if x.get("owner_id") == user["id"]]
        st.write(f"You have **{len(mine)}** listing(s).")
        if not mine:
            st.info("You haven't published a listing yet.")
        for item in mine:
            with st.container(border=True):
                render_listing_card(item)
                c1, c2 = st.columns(2)
                with c1:
                    new_status = st.selectbox(
                        "Listing status",
                        ["open", "resolved"],
                        index=0 if item.get("status") == "open" else 1,
                        key=f"status_{item['id']}",
                    )
                with c2:
                    if st.button("Save status", key=f"save_status_{item['id']}", use_container_width=True):
                        try:
                            client.table("listings").update({"status": new_status}).eq("id", item["id"]).eq("owner_id", user["id"]).execute()
                            st.success("Status updated.")
                            st.rerun()
                        except Exception as exc:
                            st.error(friendly_error(exc))

    elif page == "Claims inbox":
        st.title("Claims & connection requests")
        st.write("Requests on your listings appear in the inbox. Requests you made appear below.")
        try:
            claims = fetch_claims(client)
        except Exception as exc:
            st.error(friendly_error(exc))
            st.stop()

        owned_ids = {x["id"] for x in listings if x.get("owner_id") == user["id"]}
        received = [c for c in claims if c.get("listing_id") in owned_ids]
        sent = [c for c in claims if c.get("claimant_id") == user["id"]]

        st.subheader("Requests on my listings")
        if not received:
            st.info("No requests received yet.")
        for claim in received:
            listing = next((x for x in listings if x["id"] == claim.get("listing_id")), None)
            with st.container(border=True):
                st.markdown(f"**{listing.get('title', 'Listing') if listing else 'Listing'}** · {claim.get('status', 'pending').upper()}")
                st.write(claim.get("message", "No message"))
                st.caption(f"Request ID: {claim.get('id')}")
                if claim.get("status") == "pending":
                    new_claim_status = st.selectbox("Decision", ["pending", "accepted", "rejected"], key=f"decision_{claim['id']}")
                    if st.button("Update request", key=f"update_claim_{claim['id']}"):
                        try:
                            client.table("claims").update({"status": new_claim_status}).eq("id", claim["id"]).execute()
                            st.success("Request updated.")
                            st.rerun()
                        except Exception as exc:
                            st.error(friendly_error(exc))
                if claim.get("status") == "accepted":
                    st.info("This request was accepted. Coordinate privately and verify ownership before handing over the item.")

        st.subheader("Requests I sent")
        if not sent:
            st.info("You haven't requested to connect about any listings.")
        for claim in sent:
            listing = next((x for x in listings if x["id"] == claim.get("listing_id")), None)
            st.write(f"**{listing.get('title', 'Listing') if listing else 'Listing'}** — {claim.get('status', 'pending').upper()}")
            st.caption(claim.get("message", ""))

    st.divider()
    st.caption("FindIt is a community lost-and-found tool. Listings and suggested matches are user-submitted and should be verified before returning an item.")


if __name__ == "__main__":
    main()
