-- FindIt database setup for Supabase
-- Run this entire file in Supabase Dashboard -> SQL Editor -> New query.
-- This starter allows signed-in users to browse listings. Claims reveal only to
-- the claimant and the owner of the relevant listing.

create extension if not exists pgcrypto;

create table if not exists public.listings (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    listing_type text not null check (listing_type in ('lost', 'found')),
    title text not null check (char_length(title) between 2 and 100),
    category text not null,
    color text default '',
    description text not null check (char_length(description) between 8 and 1500),
    location text not null check (char_length(location) between 2 and 200),
    event_date date,
    image_url text,
    status text not null default 'open' check (status in ('open', 'resolved')),
    created_at timestamptz not null default now()
);

create table if not exists public.claims (
    id uuid primary key default gen_random_uuid(),
    listing_id uuid not null references public.listings(id) on delete cascade,
    claimant_id uuid not null references auth.users(id) on delete cascade,
    message text not null default '',
    status text not null default 'pending' check (status in ('pending', 'accepted', 'rejected')),
    created_at timestamptz not null default now(),
    constraint claims_no_self_claim check (claimant_id is not null)
);

create index if not exists listings_created_at_idx on public.listings (created_at desc);
create index if not exists listings_type_status_idx on public.listings (listing_type, status);
create index if not exists listings_owner_idx on public.listings (owner_id);
create index if not exists claims_listing_idx on public.claims (listing_id);
create index if not exists claims_claimant_idx on public.claims (claimant_id);

alter table public.listings enable row level security;
alter table public.claims enable row level security;

drop policy if exists "Signed-in users can read listings" on public.listings;
create policy "Signed-in users can read listings"
on public.listings for select to authenticated
using (true);

drop policy if exists "Users can create own listings" on public.listings;
create policy "Users can create own listings"
on public.listings for insert to authenticated
with check (auth.uid() = owner_id);

drop policy if exists "Owners can update own listings" on public.listings;
create policy "Owners can update own listings"
on public.listings for update to authenticated
using (auth.uid() = owner_id)
with check (auth.uid() = owner_id);

drop policy if exists "Owners can delete own listings" on public.listings;
create policy "Owners can delete own listings"
on public.listings for delete to authenticated
using (auth.uid() = owner_id);

drop policy if exists "Claimants and listing owners can read claims" on public.claims;
create policy "Claimants and listing owners can read claims"
on public.claims for select to authenticated
using (
    auth.uid() = claimant_id
    or exists (
        select 1 from public.listings l
        where l.id = claims.listing_id and l.owner_id = auth.uid()
    )
);

drop policy if exists "Users can create claims for other people's open listings" on public.claims;
create policy "Users can create claims for other people's open listings"
on public.claims for insert to authenticated
with check (
    auth.uid() = claimant_id
    and exists (
        select 1 from public.listings l
        where l.id = claims.listing_id
          and l.owner_id <> auth.uid()
          and l.status = 'open'
    )
);

drop policy if exists "Listing owners can update claim status" on public.claims;
create policy "Listing owners can update claim status"
on public.claims for update to authenticated
using (
    exists (
        select 1 from public.listings l
        where l.id = claims.listing_id and l.owner_id = auth.uid()
    )
)
with check (
    exists (
        select 1 from public.listings l
        where l.id = claims.listing_id and l.owner_id = auth.uid()
    )
);

-- Create a Storage bucket for item photos.
-- Public bucket means the photo URLs are viewable by anyone who has them.
-- Do not upload IDs, cards with visible numbers, faces, or other sensitive images.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('findit-images', 'findit-images', true, 5242880, array['image/jpeg','image/png','image/webp'])
on conflict (id) do update set
    public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "Signed-in users can upload photos to their own folder" on storage.objects;
create policy "Signed-in users can upload photos to their own folder"
on storage.objects for insert to authenticated
with check (
    bucket_id = 'findit-images'
    and (storage.foldername(name))[1] = auth.uid()::text
);

drop policy if exists "Signed-in users can replace photos in their own folder" on storage.objects;
create policy "Signed-in users can replace photos in their own folder"
on storage.objects for update to authenticated
using (
    bucket_id = 'findit-images'
    and (storage.foldername(name))[1] = auth.uid()::text
)
with check (
    bucket_id = 'findit-images'
    and (storage.foldername(name))[1] = auth.uid()::text
);

drop policy if exists "Signed-in users can delete photos in their own folder" on storage.objects;
create policy "Signed-in users can delete photos in their own folder"
on storage.objects for delete to authenticated
using (
    bucket_id = 'findit-images'
    and (storage.foldername(name))[1] = auth.uid()::text
);
