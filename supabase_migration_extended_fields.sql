-- Migration: Add extended product fields to products table
-- Run this SQL in your Supabase SQL Editor after the initial table is created

-- Add new columns for extended product information
ALTER TABLE public.products 
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS images JSONB,
ADD COLUMN IF NOT EXISTS rating DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS review_count INTEGER,
ADD COLUMN IF NOT EXISTS availability TEXT,
ADD COLUMN IF NOT EXISTS product_url TEXT,
ADD COLUMN IF NOT EXISTS currency TEXT;

-- Create index on rating for faster queries
CREATE INDEX IF NOT EXISTS idx_products_rating ON public.products(rating);

-- Create index on product_url for faster lookups
CREATE INDEX IF NOT EXISTS idx_products_url ON public.products(product_url);

-- Update comment on table
COMMENT ON TABLE public.products IS 'E-commerce products with extended information including images, ratings, and descriptions';

-- Update column comments
COMMENT ON COLUMN public.products.description IS 'Product description';
COMMENT ON COLUMN public.products.images IS 'Array of product image URLs (JSONB)';
COMMENT ON COLUMN public.products.rating IS 'Product rating (0-5 scale)';
COMMENT ON COLUMN public.products.review_count IS 'Number of reviews';
COMMENT ON COLUMN public.products.availability IS 'Product availability status';
COMMENT ON COLUMN public.products.product_url IS 'Direct URL to the product page';
COMMENT ON COLUMN public.products.currency IS 'Price currency code (e.g., USD, EUR)';

