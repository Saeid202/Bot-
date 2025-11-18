-- Supabase Table Setup for Products
-- Run this SQL in your Supabase SQL Editor

-- Create the products table
CREATE TABLE IF NOT EXISTS public.products (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price TEXT,
    source TEXT DEFAULT 'Alibaba',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create an index on source for faster queries
CREATE INDEX IF NOT EXISTS idx_products_source ON public.products(source);
CREATE INDEX IF NOT EXISTS idx_products_created_at ON public.products(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow anonymous inserts (for your bot)
-- This allows inserts using the anon key
CREATE POLICY "Allow anonymous inserts"
ON public.products
FOR INSERT
TO anon
WITH CHECK (true);

-- Create a policy to allow anonymous reads
CREATE POLICY "Allow anonymous reads"
ON public.products
FOR SELECT
TO anon
USING (true);

-- Optional: Create a policy for authenticated users (if you have auth)
-- CREATE POLICY "Allow authenticated users full access"
-- ON public.products
-- FOR ALL
-- TO authenticated
-- USING (true)
-- WITH CHECK (true);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to automatically update updated_at
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON public.products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon;
GRANT ALL ON public.products TO anon;
GRANT USAGE, SELECT ON SEQUENCE public.products_id_seq TO anon;

