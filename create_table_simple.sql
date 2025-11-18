-- Simple version - Copy and paste this into Supabase SQL Editor

-- Step 1: Create the products table
CREATE TABLE public.products (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price TEXT,
    source TEXT DEFAULT 'Alibaba',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 2: Enable Row Level Security
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;

-- Step 3: Allow anonymous inserts (so your bot can insert data)
CREATE POLICY "Allow anonymous inserts"
ON public.products
FOR INSERT
TO anon
WITH CHECK (true);

-- Step 4: Allow anonymous reads
CREATE POLICY "Allow anonymous reads"
ON public.products
FOR SELECT
TO anon
USING (true);

-- Step 5: Grant permissions
GRANT ALL ON public.products TO anon;
GRANT USAGE, SELECT ON SEQUENCE public.products_id_seq TO anon;

