-- FindIt usernames and listing-based private messaging
-- Run this in Supabase SQL Editor before deploying the matching app.py update.

create table if not exists public.profiles (
    user_id uuid primary key references auth.users(id) on delete cascade,
    username text,
    created_at timestamptz not null default now()
);

create unique index if not exists profiles_username_lower_unique
    on public.profiles (lower(username))
    where username is not null;

alter table public.profiles enable row level security;

drop policy if exists "Profiles are visible to authenticated users" on public.profiles;
create policy "Profiles are visible to authenticated users"
on public.profiles for select to authenticated
using (true);

drop policy if exists "Users can create their own profile" on public.profiles;
create policy "Users can create their own profile"
on public.profiles for insert to authenticated
with check (auth.uid() = user_id);

drop policy if exists "Users can update their own profile" on public.profiles;
create policy "Users can update their own profile"
on public.profiles for update to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create table if not exists public.conversations (
    id uuid primary key default gen_random_uuid(),
    listing_id text not null,
    starter_id uuid not null references auth.users(id) on delete cascade,
    owner_id uuid not null references auth.users(id) on delete cascade,
    created_at timestamptz not null default now(),
    constraint conversations_distinct_users check (starter_id <> owner_id),
    constraint conversations_listing_starter_unique unique (listing_id, starter_id)
);

create index if not exists conversations_starter_idx on public.conversations(starter_id);
create index if not exists conversations_owner_idx on public.conversations(owner_id);

alter table public.conversations enable row level security;

drop policy if exists "Participants can view conversations" on public.conversations;
create policy "Participants can view conversations"
on public.conversations for select to authenticated
using (auth.uid() = starter_id or auth.uid() = owner_id);

drop policy if exists "Listing users can start conversations" on public.conversations;
create policy "Listing users can start conversations"
on public.conversations for insert to authenticated
with check (
    auth.uid() = starter_id
    and starter_id <> owner_id
    and exists (
        select 1 from public.listings l
        where l.id::text = listing_id
          and l.owner_id = owner_id
          and l.status = 'open'
    )
);

create table if not exists public.messages (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references public.conversations(id) on delete cascade,
    sender_id uuid not null references auth.users(id) on delete cascade,
    body text not null check (char_length(trim(body)) between 1 and 2000),
    created_at timestamptz not null default now()
);

create index if not exists messages_conversation_created_idx
    on public.messages(conversation_id, created_at);

alter table public.messages enable row level security;

drop policy if exists "Participants can read messages" on public.messages;
create policy "Participants can read messages"
on public.messages for select to authenticated
using (
    exists (
        select 1 from public.conversations c
        where c.id = conversation_id
          and (auth.uid() = c.starter_id or auth.uid() = c.owner_id)
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
    )
);

-- Create blank profiles for existing accounts. They choose a username at next login.
insert into public.profiles (user_id)
select id from auth.users
on conflict (user_id) do nothing;

-- Automatically create a profile for future signups using signup metadata.
create or replace function public.findit_create_profile()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    insert into public.profiles (user_id, username)
    values (
        new.id,
        nullif(trim(new.raw_user_meta_data ->> 'username'), '')
    )
    on conflict (user_id) do nothing;
    return new;
end;
$$;

drop trigger if exists findit_auth_user_profile on auth.users;
create trigger findit_auth_user_profile
after insert on auth.users
for each row execute procedure public.findit_create_profile();

grant select, insert, update on public.profiles to authenticated;
grant select, insert on public.conversations to authenticated;
grant select, insert on public.messages to authenticated;

-- Enable database change broadcasts for the live chat.
-- Safe to run more than once; does not change existing tables or data.
DO $findit_realtime$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_publication_tables
        WHERE pubname = 'supabase_realtime'
          AND schemaname = 'public'
          AND tablename = 'messages'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.messages;
    END IF;
END;
$findit_realtime$;
