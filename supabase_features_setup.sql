-- FindIt feature expansion migration
-- Run AFTER supabase_messaging_setup.sql in Supabase SQL Editor.
-- Additive and rerunnable: preserves existing accounts, listings, claims and messages.

create extension if not exists pgcrypto;

-- 1) Saved listings
create table if not exists public.saved_listings (
    user_id uuid not null references auth.users(id) on delete cascade,
    listing_id uuid not null references public.listings(id) on delete cascade,
    created_at timestamptz not null default now(),
    primary key (user_id, listing_id)
);
create index if not exists saved_listings_listing_idx on public.saved_listings(listing_id);
alter table public.saved_listings enable row level security;
drop policy if exists "Users manage their own saved listings" on public.saved_listings;
create policy "Users manage their own saved listings"
on public.saved_listings for all to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);
grant select, insert, delete on public.saved_listings to authenticated;

-- 2) Notifications
create table if not exists public.notifications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    notification_type text not null default 'general',
    title text not null,
    body text not null default '',
    listing_id uuid references public.listings(id) on delete set null,
    event_key text not null,
    read_at timestamptz,
    created_at timestamptz not null default now(),
    constraint notifications_user_event_unique unique (user_id, event_key)
);
create index if not exists notifications_user_created_idx
    on public.notifications(user_id, created_at desc);
alter table public.notifications enable row level security;
drop policy if exists "Users read their own notifications" on public.notifications;
create policy "Users read their own notifications"
on public.notifications for select to authenticated
using (auth.uid() = user_id);
drop policy if exists "Users mark their own notifications read" on public.notifications;
create policy "Users mark their own notifications read"
on public.notifications for update to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);
drop policy if exists "Users create their own app notifications" on public.notifications;
create policy "Users create their own app notifications"
on public.notifications for insert to authenticated
with check (auth.uid() = user_id);
grant select, insert, update on public.notifications to authenticated;

-- 3) Saved search alerts
create table if not exists public.search_alerts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    keywords text not null check (char_length(trim(keywords)) between 2 and 100),
    category text not null default 'All categories',
    listing_type text not null default 'any'
        check (listing_type in ('any', 'lost', 'found')),
    location text not null default '',
    enabled boolean not null default true,
    created_at timestamptz not null default now()
);
create index if not exists search_alerts_user_idx on public.search_alerts(user_id, created_at desc);
alter table public.search_alerts enable row level security;
drop policy if exists "Users manage their own search alerts" on public.search_alerts;
create policy "Users manage their own search alerts"
on public.search_alerts for all to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);
grant select, insert, update, delete on public.search_alerts to authenticated;

-- 4) Private ownership-verification details.
-- The table is separate from listings so public listing reads never reveal these details.
create table if not exists public.listing_verification (
    listing_id uuid primary key references public.listings(id) on delete cascade,
    owner_id uuid not null references auth.users(id) on delete cascade,
    private_detail text not null check (char_length(trim(private_detail)) between 3 and 500),
    updated_at timestamptz not null default now()
);
alter table public.listing_verification enable row level security;
drop policy if exists "Only listing owners can view verification details" on public.listing_verification;
create policy "Only listing owners can view verification details"
on public.listing_verification for select to authenticated
using (auth.uid() = owner_id);
drop policy if exists "Listing owners manage verification details" on public.listing_verification;
create policy "Listing owners manage verification details"
on public.listing_verification for all to authenticated
using (
    auth.uid() = owner_id
    and exists (select 1 from public.listings l where l.id = listing_id and l.owner_id = auth.uid())
)
with check (
    auth.uid() = owner_id
    and exists (select 1 from public.listings l where l.id = listing_id and l.owner_id = auth.uid())
);
grant select, insert, update, delete on public.listing_verification to authenticated;

-- 5) User blocks and community reports
create table if not exists public.blocked_users (
    blocker_id uuid not null references auth.users(id) on delete cascade,
    blocked_user_id uuid not null references auth.users(id) on delete cascade,
    created_at timestamptz not null default now(),
    primary key (blocker_id, blocked_user_id),
    constraint blocked_users_not_self check (blocker_id <> blocked_user_id)
);
alter table public.blocked_users enable row level security;
drop policy if exists "Users manage blocks they created" on public.blocked_users;
create policy "Users manage blocks they created"
on public.blocked_users for all to authenticated
using (auth.uid() = blocker_id)
with check (auth.uid() = blocker_id and blocker_id <> blocked_user_id);
grant select, insert, delete on public.blocked_users to authenticated;

create or replace function public.findit_users_blocked(user_a uuid, user_b uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $findit$
    select
        (auth.uid() = user_a or auth.uid() = user_b)
        and exists (
            select 1
            from public.blocked_users b
            where (b.blocker_id = user_a and b.blocked_user_id = user_b)
               or (b.blocker_id = user_b and b.blocked_user_id = user_a)
        );
$findit$;
revoke all on function public.findit_users_blocked(uuid, uuid) from public;
grant execute on function public.findit_users_blocked(uuid, uuid) to authenticated;

create table if not exists public.user_reports (
    id uuid primary key default gen_random_uuid(),
    reporter_id uuid not null references auth.users(id) on delete cascade,
    reported_user_id uuid references auth.users(id) on delete set null,
    listing_id uuid references public.listings(id) on delete set null,
    reason text not null,
    details text not null default '',
    status text not null default 'open' check (status in ('open', 'reviewed', 'dismissed')),
    created_at timestamptz not null default now(),
    constraint user_reports_target_required check (reported_user_id is not null or listing_id is not null)
);
create index if not exists user_reports_created_idx on public.user_reports(created_at desc);
alter table public.user_reports enable row level security;
drop policy if exists "Users submit reports" on public.user_reports;
create policy "Users submit reports"
on public.user_reports for insert to authenticated
with check (
    auth.uid() = reporter_id
    and (reported_user_id is null or reported_user_id <> auth.uid())
);
drop policy if exists "Users view reports they submitted" on public.user_reports;
create policy "Users view reports they submitted"
on public.user_reports for select to authenticated
using (auth.uid() = reporter_id);
grant select, insert on public.user_reports to authenticated;

-- 6) Optional approximate coordinates for map discovery. Existing rows stay valid.
alter table public.listings add column if not exists approximate_lat double precision;
alter table public.listings add column if not exists approximate_lng double precision;
do $findit_coords$
begin
    if not exists (
        select 1 from pg_constraint
        where conrelid = 'public.listings'::regclass
          and conname = 'listings_approximate_coordinates_check'
    ) then
        alter table public.listings
        add constraint listings_approximate_coordinates_check check (
            (approximate_lat is null and approximate_lng is null)
            or (
                approximate_lat between -90 and 90
                and approximate_lng between -180 and 180
            )
        );
    end if;
end;
$findit_coords$;

-- 7) Automatic notifications for claims, messages, saved-listing updates and search alerts.
create or replace function public.findit_notify_claim_activity()
returns trigger
language plpgsql
security definer
set search_path = ''
as $findit$
declare
    listing_owner uuid;
begin
    select l.owner_id into listing_owner
    from public.listings l
    where l.id = new.listing_id;

    if tg_op = 'INSERT' then
        if listing_owner is not null then
            insert into public.notifications(user_id, notification_type, title, body, listing_id, event_key)
            values (
                listing_owner, 'claim', 'New claim request',
                'Someone sent a request about one of your listings.',
                new.listing_id, 'claim:new:' || new.id::text
            ) on conflict (user_id, event_key) do nothing;
        end if;
    elsif tg_op = 'UPDATE' and new.status is distinct from old.status then
        insert into public.notifications(user_id, notification_type, title, body, listing_id, event_key)
        values (
            new.claimant_id, 'claim', 'Claim status updated',
            'Your claim is now ' || upper(new.status) || '.',
            new.listing_id, 'claim:status:' || new.id::text || ':' || new.status
        ) on conflict (user_id, event_key) do nothing;
    end if;
    return new;
end;
$findit$;

drop trigger if exists findit_claim_notifications on public.claims;
create trigger findit_claim_notifications
after insert or update of status on public.claims
for each row execute function public.findit_notify_claim_activity();

create or replace function public.findit_notify_new_message()
returns trigger
language plpgsql
security definer
set search_path = ''
as $findit$
declare
    recipient uuid;
    linked_listing text;
begin
    select
        case when new.sender_id = c.starter_id then c.owner_id else c.starter_id end,
        c.listing_id
    into recipient, linked_listing
    from public.conversations c
    where c.id = new.conversation_id;

    if recipient is not null then
        insert into public.notifications(user_id, notification_type, title, body, listing_id, event_key)
        values (
            recipient, 'message', 'New message',
            'You received a new message about a listing.',
            case when linked_listing ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                 then linked_listing::uuid else null end,
            'message:' || new.id::text
        ) on conflict (user_id, event_key) do nothing;
    end if;
    return new;
end;
$findit$;

drop trigger if exists findit_message_notifications on public.messages;
create trigger findit_message_notifications
after insert on public.messages
for each row execute function public.findit_notify_new_message();

create or replace function public.findit_notify_search_alerts()
returns trigger
language plpgsql
security definer
set search_path = ''
as $findit$
declare
    alert record;
    searchable text;
begin
    searchable := lower(concat_ws(' ', new.title, new.description, new.category, new.color, new.location));
    for alert in
        select * from public.search_alerts a
        where a.enabled
          and a.user_id <> new.owner_id
          and (a.listing_type = 'any' or a.listing_type = new.listing_type)
          and (a.category = 'All categories' or lower(a.category) = lower(new.category))
          and (trim(a.location) = '' or searchable like '%' || lower(trim(a.location)) || '%')
          and searchable like '%' || lower(trim(a.keywords)) || '%'
    loop
        insert into public.notifications(user_id, notification_type, title, body, listing_id, event_key)
        values (
            alert.user_id, 'search', 'A saved search has a new match',
            'A new listing matches your saved search: ' || alert.keywords,
            new.id, 'search:' || alert.id::text || ':' || new.id::text
        ) on conflict (user_id, event_key) do nothing;
    end loop;
    return new;
end;
$findit$;

drop trigger if exists findit_search_alert_notifications on public.listings;
create trigger findit_search_alert_notifications
after insert on public.listings
for each row execute function public.findit_notify_search_alerts();

-- Notify both participants when a newly published listing is a strong
-- category/text/colour/location/date candidate for an opposite-type report.
create or replace function public.findit_notify_possible_matches()
returns trigger
language plpgsql
security definer
set search_path = ''
as $findit$
declare
    candidate record;
begin
    for candidate in
        select l.id, l.owner_id, l.title
        from public.listings l
        where l.status = 'open'
          and l.id <> new.id
          and l.owner_id <> new.owner_id
          and l.listing_type <> new.listing_type
          and lower(l.category) = lower(new.category)
          and (
              lower(l.title) like '%' || lower(new.title) || '%'
              or lower(new.title) like '%' || lower(l.title) || '%'
              or lower(l.description) like '%' || lower(new.title) || '%'
              or lower(new.description) like '%' || lower(l.title) || '%'
              or (
                  coalesce(trim(l.color), '') <> ''
                  and coalesce(trim(new.color), '') <> ''
                  and lower(l.color) = lower(new.color)
              )
          )
          and (
              l.event_date is null
              or new.event_date is null
              or abs(l.event_date - new.event_date) <= 30
          )
          and (
              lower(l.location) like '%' || lower(new.location) || '%'
              or lower(new.location) like '%' || lower(l.location) || '%'
          )
    loop
        insert into public.notifications(
            user_id, notification_type, title, body, listing_id, event_key
        )
        values (
            candidate.owner_id,
            'match',
            'A possible match was found',
            'A new ' || upper(new.listing_type) || ' report may match your listing: ' || candidate.title,
            new.id,
            'match:' || candidate.id::text || ':' || new.id::text
        )
        on conflict (user_id, event_key) do nothing;

        insert into public.notifications(
            user_id, notification_type, title, body, listing_id, event_key
        )
        values (
            new.owner_id,
            'match',
            'A possible match was found',
            'Your new report may match this listing: ' || candidate.title,
            candidate.id,
            'match:' || new.id::text || ':' || candidate.id::text
        )
        on conflict (user_id, event_key) do nothing;
    end loop;
    return new;
end;
$findit$;

drop trigger if exists findit_possible_match_notifications on public.listings;
create trigger findit_possible_match_notifications
after insert on public.listings
for each row execute function public.findit_notify_possible_matches();

create or replace function public.findit_notify_saved_listing_update()
returns trigger
language plpgsql
security definer
set search_path = ''
as $findit$
declare
    saved_user record;
begin
    if new.status is distinct from old.status
       or new.title is distinct from old.title
       or new.description is distinct from old.description
       or new.location is distinct from old.location then
        for saved_user in
            select s.user_id from public.saved_listings s
            where s.listing_id = new.id and s.user_id <> new.owner_id
        loop
            insert into public.notifications(user_id, notification_type, title, body, listing_id, event_key)
            values (
                saved_user.user_id, 'saved', 'A saved listing was updated',
                'A listing in your saved items has changed.',
                new.id,
                'saved-update:' || new.id::text || ':' || to_char(clock_timestamp(), 'YYYYMMDDHH24MISSMS')
            ) on conflict (user_id, event_key) do nothing;
        end loop;
    end if;
    return new;
end;
$findit$;

drop trigger if exists findit_saved_listing_notifications on public.listings;
create trigger findit_saved_listing_notifications
after update on public.listings
for each row execute function public.findit_notify_saved_listing_update();

-- 8) Prevent participants from reading or writing conversations/messages after either party blocks the other.
drop policy if exists "Participants can view conversations" on public.conversations;
create policy "Participants can view conversations"
on public.conversations for select to authenticated
using (
    (auth.uid() = starter_id or auth.uid() = owner_id)
    and not public.findit_users_blocked(starter_id, owner_id)
);
drop policy if exists "Listing users can start conversations" on public.conversations;
create policy "Listing users can start conversations"
on public.conversations for insert to authenticated
with check (
    auth.uid() = starter_id
    and starter_id <> owner_id
    and not public.findit_users_blocked(starter_id, owner_id)
    and exists (
        select 1 from public.listings l
        where l.id::text = listing_id
          and l.owner_id = owner_id
          and l.status = 'open'
    )
);
drop policy if exists "Participants can read messages" on public.messages;
create policy "Participants can read messages"
on public.messages for select to authenticated
using (
    exists (
        select 1 from public.conversations c
        where c.id = conversation_id
          and (auth.uid() = c.starter_id or auth.uid() = c.owner_id)
          and not public.findit_users_blocked(c.starter_id, c.owner_id)
    )
);
drop policy if exists "Participants can send messages" on public.messages;
create policy "Participants can send messages"
on public.messages for insert to authenticated
with check (
    auth.uid() = sender_id
    and exists (
        select 1 from public.conversations c
        where c.id = conversation_id
          and (auth.uid() = c.starter_id or auth.uid() = c.owner_id)
          and not public.findit_users_blocked(c.starter_id, c.owner_id)
    )
);

-- Grant function execution through Postgres triggers; RLS remains enforced on user-facing tables.
