"""Additional FindIt features: matching, saves, notifications, map, profiles and safety."""
from datetime import date, datetime, timezone
from difflib import SequenceMatcher
from io import BytesIO
import re

import qrcode
import streamlit as st


_STOP_WORDS = {
    "the", "a", "an", "and", "or", "with", "my", "is", "it", "of", "to",
    "in", "on", "at", "for", "near", "was", "were", "this", "that", "item",
    "lost", "found", "have", "has", "from", "with", "nearby", "around",
}


def _tokens(value):
    return {
        token for token in re.findall(r"[a-z0-9]+", str(value or "").lower())
        if len(token) > 1 and token not in _STOP_WORDS
    }


def _ratio(a, b):
    a = " ".join(sorted(_tokens(a)))
    b = " ".join(sorted(_tokens(b)))
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _jaccard(a, b):
    left, right = _tokens(a), _tokens(b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _date_distance(a, b):
    try:
        da = date.fromisoformat(str(a)[:10])
        db = date.fromisoformat(str(b)[:10])
        return abs((da - db).days)
    except (TypeError, ValueError):
        return None


def score_match(lost, found):
    """Explainable 0–100 rule-based score; this is not an AI prediction."""
    if lost.get("listing_type") != "lost" or found.get("listing_type") != "found":
        return 0

    score = 0.0
    if lost.get("category") and str(lost.get("category")).lower() == str(found.get("category")).lower():
        score += 20

    color_left, color_right = lost.get("color"), found.get("color")
    if color_left and color_right:
        score += 15 * max(_ratio(color_left, color_right), _jaccard(color_left, color_right))

    title_left = lost.get("title", "")
    title_right = found.get("title", "")
    score += 20 * max(_ratio(title_left, title_right), _jaccard(title_left, title_right))

    desc_left = f"{title_left} {lost.get('description', '')}"
    desc_right = f"{title_right} {found.get('description', '')}"
    score += 15 * _jaccard(desc_left, desc_right)

    location_left, location_right = lost.get("location"), found.get("location")
    if location_left and location_right:
        score += 20 * max(_ratio(location_left, location_right), _jaccard(location_left, location_right))

    days = _date_distance(lost.get("event_date"), found.get("event_date"))
    if days is not None:
        score += 10 if days <= 2 else 7 if days <= 7 else 4 if days <= 30 else 0

    return int(round(min(100, score)))


def score_duplicate(candidate, existing):
    """Similarity score for two reports of the same type, used as a warning."""
    if candidate.get("listing_type") != existing.get("listing_type"):
        return 0

    score = 0.0
    if str(candidate.get("category", "")).lower() == str(existing.get("category", "")).lower():
        score += 20

    title_a, title_b = candidate.get("title", ""), existing.get("title", "")
    score += 30 * max(_ratio(title_a, title_b), _jaccard(title_a, title_b))

    desc_a = f"{title_a} {candidate.get('description', '')}"
    desc_b = f"{title_b} {existing.get('description', '')}"
    score += 15 * _jaccard(desc_a, desc_b)

    if candidate.get("color") and existing.get("color"):
        score += 15 * max(_ratio(candidate.get("color"), existing.get("color")),
                          _jaccard(candidate.get("color"), existing.get("color")))

    if candidate.get("location") and existing.get("location"):
        score += 15 * max(_ratio(candidate.get("location"), existing.get("location")),
                          _jaccard(candidate.get("location"), existing.get("location")))

    days = _date_distance(candidate.get("event_date"), existing.get("event_date"))
    if days is not None:
        score += 5 if days <= 1 else 3 if days <= 7 else 0

    return int(round(min(100, score)))


def find_duplicates(candidate, listings, user_id, limit=4):
    results = []
    for item in listings:
        if item.get("owner_id") == user_id or item.get("status") != "open":
            continue
        score = score_duplicate(candidate, item)
        if score >= 45:
            results.append((score, item))
    return sorted(results, key=lambda pair: pair[0], reverse=True)[:limit]


def get_blocked_user_ids(client, user_id):
    try:
        rows = client.table("blocked_users").select("blocked_user_id").eq(
            "blocker_id", user_id
        ).execute().data or []
        return {row["blocked_user_id"] for row in rows}
    except Exception:
        return set()


def get_saved_listing_ids(client, user_id):
    try:
        rows = client.table("saved_listings").select("listing_id").eq(
            "user_id", user_id
        ).execute().data or []
        return {str(row["listing_id"]) for row in rows}
    except Exception:
        return set()


def get_unread_notification_count(client, user_id):
    try:
        rows = client.table("notifications").select("id").eq(
            "user_id", user_id
        ).is_("read_at", "null").execute().data or []
        return len(rows)
    except Exception:
        return 0


def get_app_base_url():
    base = None
    try:
        base = st.secrets.get("app", {}).get("base_url")
    except Exception:
        pass
    if not base:
        try:
            base = st.context.url
        except Exception:
            base = None
    if not base:
        return None
    return str(base).split("?", 1)[0].rstrip("/")


def render_listing_actions(client, user, item, saved_ids, base_url):
    """Save, share, report and block actions for a public listing."""
    listing_id = str(item["id"])
    owner_id = item.get("owner_id")
    is_own = owner_id == user["id"]

    action_cols = st.columns([1, 1] if not is_own else [1])
    if not is_own:
        with action_cols[0]:
            is_saved = listing_id in saved_ids
            if st.button(
                "★ Saved" if is_saved else "☆ Save item",
                key=f"save_listing_{listing_id}",
                use_container_width=True,
            ):
                try:
                    if is_saved:
                        client.table("saved_listings").delete().eq(
                            "user_id", user["id"]
                        ).eq("listing_id", listing_id).execute()
                    else:
                        client.table("saved_listings").insert({
                            "user_id": user["id"],
                            "listing_id": listing_id,
                        }).execute()
                    st.rerun()
                except Exception as exc:
                    st.error("Couldn't update saved items. " + str(exc)[:220])

    qr_col = action_cols[-1]
    with qr_col:
        with st.expander("QR & share", expanded=False):
            if not base_url:
                st.info("Add [app].base_url to Streamlit secrets to create shareable QR codes.")
            else:
                share_url = f"{base_url}?listing={listing_id}"
                qr = qrcode.QRCode(box_size=6, border=3)
                qr.add_data(share_url)
                qr.make(fit=True)
                qr_image = qr.make_image(fill_color="#172033", back_color="white").get_image()
                buffer = BytesIO()
                qr_image.save(buffer, format="PNG")
                st.image(buffer.getvalue(), caption="Scan to open this FindIt listing", width=190)
                st.download_button(
                    "Download QR code",
                    data=buffer.getvalue(),
                    file_name=f"findit-{listing_id[:8]}.png",
                    mime="image/png",
                    key=f"download_qr_{listing_id}",
                    use_container_width=True,
                )
                st.code(share_url, language=None)

    if not is_own:
        with st.expander("Safety options", expanded=False):
            st.markdown("**Report this listing or account**")
            with st.form(f"report_listing_form_{listing_id}"):
                reason = st.selectbox(
                    "Reason",
                    ["Suspicious or misleading listing", "Scam or impersonation",
                     "Inappropriate content", "Duplicate listing", "Other"],
                    key=f"report_reason_{listing_id}",
                )
                details = st.text_area(
                    "Additional details (optional)",
                    max_chars=1000,
                    key=f"report_details_{listing_id}",
                )
                submit_report = st.form_submit_button("Submit report")
                if submit_report:
                    try:
                        client.table("user_reports").insert({
                            "reporter_id": user["id"],
                            "reported_user_id": owner_id,
                            "listing_id": listing_id,
                            "reason": reason,
                            "details": details.strip(),
                        }).execute()
                        st.success("Report submitted for admin review.")
                    except Exception as exc:
                        st.error("Couldn't submit report. " + str(exc)[:220])

            if st.button("Block this user", key=f"block_user_{owner_id}_{listing_id}"):
                try:
                    already = client.table("blocked_users").select("blocked_user_id").eq(
                        "blocker_id", user["id"]
                    ).eq("blocked_user_id", owner_id).execute().data or []
                    if not already:
                        client.table("blocked_users").insert({
                            "blocker_id": user["id"],
                            "blocked_user_id": owner_id,
                        }).execute()
                    st.success("User blocked. Their listings and conversations will be hidden.")
                    st.rerun()
                except Exception as exc:
                    st.error("Couldn't block this user. " + str(exc)[:220])


def render_smart_matches_page(user, listings, start_conversation):
    st.markdown("### Matches for your reports")
    st.caption(
        "FindIt compares category, colour, item wording, location and date. "
        "Scores are rule-based suggestions, not proof of ownership."
    )
    own = [
        x for x in listings
        if x.get("owner_id") == user["id"] and x.get("status") == "open"
    ]
    pairs = []
    for mine in own:
        opposite_type = "found" if mine.get("listing_type") == "lost" else "lost"
        for other in listings:
            if other.get("owner_id") == user["id"] or other.get("status") != "open":
                continue
            if other.get("listing_type") != opposite_type:
                continue
            lost, found = (mine, other) if mine.get("listing_type") == "lost" else (other, mine)
            score = score_match(lost, found)
            if score >= 25:
                pairs.append((score, mine, other))

    pairs.sort(key=lambda row: row[0], reverse=True)
    if not pairs:
        st.info("No likely matches yet. Keep your report open while more items are added.")
        return

    for score, mine, other in pairs[:30]:
        event_key = f"match:{mine['id']}:{other['id']}"
        try:
            client = st.session_state.get("_supabase_client")
            if client:
                client.table("notifications").upsert({
                    "user_id": user["id"],
                    "notification_type": "match",
                    "title": "A possible match was found",
                    "body": f"{other.get('title', 'A listing')} may match your {mine.get('title', 'report')}.",
                    "listing_id": other["id"],
                    "event_key": event_key,
                }, on_conflict="user_id,event_key").execute()
        except Exception:
            pass

        with st.container(border=True):
            top, action = st.columns([3, 1])
            with top:
                st.markdown(f"**{score}% match · {mine.get('title')} ↔ {other.get('title')}**")
                st.caption(
                    f"Your {mine.get('listing_type')} report: {mine.get('location', 'Unknown location')} · "
                    f"Other report: {other.get('location', 'Unknown location')}"
                )
                st.write(other.get("description") or "No description provided.")
                st.caption(
                    "Compare details privately before arranging a handover. "
                    "A match score is not verification."
                )
            with action:
                if other.get("image_url"):
                    st.image(other["image_url"], use_container_width=True)
                if st.button("Message poster", key=f"match_message_{mine['id']}_{other['id']}",
                             use_container_width=True):
                    start_conversation(other)


def render_saved_items_page(client, user, listings, render_card):
    st.markdown("### Your saved listings")
    saved_ids = get_saved_listing_ids(client, user["id"])
    saved = [item for item in listings if str(item["id"]) in saved_ids]
    if not saved:
        st.info("You haven't saved any listings yet. Use ☆ Save item while exploring.")
        return saved_ids
    st.caption(f"{len(saved)} saved listing(s)")
    for item in saved:
        render_card(item)
    return saved_ids


def render_notifications_page(client, user):
    st.markdown("### Your notifications")
    inbox_tab, alerts_tab = st.tabs(["Inbox", "Saved searches"])
    with inbox_tab:
        rows = client.table("notifications").select("*").eq(
            "user_id", user["id"]
        ).order("created_at", desc=True).limit(100).execute().data or []
        unread = [n for n in rows if not n.get("read_at")]
        if unread and st.button("Mark all as read", key="mark_all_notifications"):
            client.table("notifications").update({
                "read_at": datetime.now(timezone.utc).isoformat()
            }).eq("user_id", user["id"]).is_("read_at", "null").execute()
            st.rerun()
        if not rows:
            st.info("You're all caught up. New messages, claims and saved-search matches will appear here.")
        for row in rows:
            with st.container(border=True):
                st.markdown(f"**{row.get('title', 'Notification')}**")
                st.write(row.get("body") or "")
                st.caption(str(row.get("created_at", "")).replace("T", " ")[:16])
                c1, c2 = st.columns([1, 4])
                with c1:
                    if not row.get("read_at") and st.button("Mark read", key=f"read_notification_{row['id']}"):
                        client.table("notifications").update({
                            "read_at": datetime.now(timezone.utc).isoformat()
                        }).eq("id", row["id"]).eq("user_id", user["id"]).execute()
                        st.rerun()
                with c2:
                    if row.get("listing_id") and st.button("View listing", key=f"view_notification_{row['id']}"):
                        st.query_params["listing"] = str(row["listing_id"])
                        st.session_state["main_navigation"] = "Home & Search"
                        st.rerun()

    with alerts_tab:
        st.caption("Get an in-app notification when a new listing matches these filters.")
        with st.form("create_search_alert_form", clear_on_submit=True):
            keywords = st.text_input("Keywords", placeholder="e.g. black wallet")
            category = st.selectbox("Category", [
                "All categories", "Electronics", "Wallet / Cards", "Keys", "Bag",
                "Clothing", "Books / Stationery", "Jewellery", "Bottle / Container", "Other"
            ])
            listing_type = st.selectbox("Report type", ["Any type", "Lost", "Found"])
            location = st.text_input("Location contains (optional)", placeholder="e.g. library")
            create_alert = st.form_submit_button("Create search alert", type="primary")
            if create_alert:
                if len(keywords.strip()) < 2:
                    st.error("Enter at least two characters for the keyword search.")
                else:
                    client.table("search_alerts").insert({
                        "user_id": user["id"],
                        "keywords": keywords.strip()[:100],
                        "category": category,
                        "listing_type": listing_type.lower().replace("any type", "any"),
                        "location": location.strip()[:200],
                    }).execute()
                    st.success("Search alert created.")
                    st.rerun()

        alerts = client.table("search_alerts").select("*").eq(
            "user_id", user["id"]
        ).order("created_at", desc=True).execute().data or []
        if not alerts:
            st.info("No saved searches yet.")
        for alert in alerts:
            with st.container(border=True):
                st.markdown(f"**{alert['keywords']}**")
                st.caption(
                    f"{alert.get('category', 'All categories')} · "
                    f"{alert.get('listing_type', 'any').title()} · "
                    f"{alert.get('location') or 'Any location'}"
                )
                left, right = st.columns(2)
                with left:
                    if st.button(
                        "Disable" if alert.get("enabled", True) else "Enable",
                        key=f"toggle_alert_{alert['id']}",
                        use_container_width=True,
                    ):
                        client.table("search_alerts").update({
                            "enabled": not alert.get("enabled", True)
                        }).eq("id", alert["id"]).eq("user_id", user["id"]).execute()
                        st.rerun()
                with right:
                    if st.button("Delete", key=f"delete_alert_{alert['id']}",
                                 use_container_width=True):
                        client.table("search_alerts").delete().eq(
                            "id", alert["id"]
                        ).eq("user_id", user["id"]).execute()
                        st.rerun()


def render_map_page(listings):
    st.markdown("### Map discovery")
    st.caption(
        "Only listings with optional approximate coordinates appear here. "
        "Posters should use a nearby landmark or a broad campus area, never a home address."
    )
    available = [
        item for item in listings
        if item.get("status") == "open"
        and item.get("approximate_lat") is not None
        and item.get("approximate_lng") is not None
    ]
    if not available:
        st.info(
            "No listings have approximate map coordinates yet. When reporting an item, "
            "posters can optionally add approximate latitude and longitude."
        )
        return

    f1, f2 = st.columns(2)
    with f1:
        kind = st.selectbox("Report type", ["All", "Lost", "Found"], key="map_type_filter")
    with f2:
        category = st.selectbox(
            "Category",
            ["All categories"] + sorted({str(x.get("category", "Other")) for x in available}),
            key="map_category_filter",
        )
    shown = [
        x for x in available
        if (kind == "All" or x.get("listing_type") == kind.lower())
        and (category == "All categories" or x.get("category") == category)
    ]
    if shown:
        map_data = [{
            "lat": float(x["approximate_lat"]),
            "lon": float(x["approximate_lng"]),
        } for x in shown]
        st.map(map_data, use_container_width=True)
        for item in shown:
            st.markdown(
                f"**{item.get('title', 'Item')}** · {item.get('listing_type', '').upper()} "
                f"· {item.get('location', 'Location not specified')}"
            )
    else:
        st.info("No listings match those map filters.")


def render_profile_page(client, user, listings):
    st.markdown("### Your community profile")
    profile = client.table("profiles").select("user_id, username, created_at").eq(
        "user_id", user["id"]
    ).limit(1).execute().data
    profile = profile[0] if profile else {}
    own = [x for x in listings if x.get("owner_id") == user["id"]]
    resolved_found = [
        x for x in own if x.get("listing_type") == "found" and x.get("status") == "resolved"
    ]
    helped = len(resolved_found)
    created = len(own)

    st.subheader("@" + str(profile.get("username") or user.get("username", "member")))
    if profile.get("created_at"):
        st.caption("FindIt member since " + str(profile["created_at"])[:10])
    m1, m2, m3 = st.columns(3)
    m1.metric("Reports posted", created)
    m2.metric("Resolved found items", helped)
    m3.metric("Open reports", sum(1 for x in own if x.get("status") == "open"))

    st.markdown("**Community badges**")
    badges = []
    if created >= 1:
        badges.append(("🧭", "First report", "Published a first lost-or-found report"))
    if created >= 5:
        badges.append(("🌟", "Active member", "Published five or more reports"))
    if helped >= 1:
        badges.append(("🤝", "Helpful finder", "Marked a found-item report as resolved"))
    if helped >= 3:
        badges.append(("🏅", "Community champion", "Helped return at least three found items"))
    if not badges:
        st.info("Your first report will unlock your first community badge.")
    else:
        cols = st.columns(min(2, len(badges)))
        for index, (emoji, title, desc) in enumerate(badges):
            with cols[index % len(cols)]:
                with st.container(border=True):
                    st.markdown(f"### {emoji} {title}")
                    st.caption(desc)

    st.divider()
    with st.expander("Community member directory", expanded=False):
        search_member = st.text_input(
            "Find a member by username",
            placeholder="Search usernames...",
            key="community_member_search",
        ).strip().lower()
        members = client.table("profiles").select(
            "user_id, username, created_at"
        ).order("created_at", desc=True).limit(100).execute().data or []
        counts = {}
        helpful = set()
        for item in listings:
            owner = item.get("owner_id")
            if owner:
                counts[owner] = counts.get(owner, 0) + 1
                if item.get("listing_type") == "found" and item.get("status") == "resolved":
                    helpful.add(owner)
        visible_members = [
            member for member in members
            if member.get("username")
            and search_member in member.get("username", "").lower()
        ]
        if not visible_members:
            st.caption("No members match that username.")
        else:
            for member in visible_members:
                member_id = member["user_id"]
                if member_id == user["id"]:
                    continue
                member_name = member.get("username") or "FindIt member"
                member_badges = []
                if counts.get(member_id, 0) >= 5:
                    member_badges.append("🌟 Active member")
                if member_id in helpful:
                    member_badges.append("🤝 Helpful finder")
                with st.container(border=True):
                    st.markdown(f"**@{member_name}**")
                    st.caption(
                        f"{counts.get(member_id, 0)} public report(s) · "
                        f"Member since {str(member.get('created_at', ''))[:10]}"
                    )
                    if member_badges:
                        st.caption(" · ".join(member_badges))
                    else:
                        st.caption("Community member")

    st.divider()
    st.markdown("**Blocked accounts**")
    blocked = client.table("blocked_users").select("blocked_user_id").eq(
        "blocker_id", user["id"]
    ).execute().data or []
    if not blocked:
        st.caption("You haven't blocked anyone.")
    else:
        ids = [x["blocked_user_id"] for x in blocked]
        profiles = client.table("profiles").select("user_id, username").in_(
            "user_id", ids
        ).execute().data or []
        names = {x["user_id"]: x.get("username") or "FindIt member" for x in profiles}
        for blocked_id in ids:
            c1, c2 = st.columns([3, 1])
            c1.write("@" + names.get(blocked_id, "member"))
            if c2.button("Unblock", key=f"unblock_{blocked_id}"):
                client.table("blocked_users").delete().eq(
                    "blocker_id", user["id"]
                ).eq("blocked_user_id", blocked_id).execute()
                st.success("Account unblocked.")
                st.rerun()
