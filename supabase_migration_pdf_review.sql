-- Migration: Add PDF review and approval workflow fields
-- Run this SQL in your Supabase SQL Editor

-- Add status and PDF-related columns to products table
ALTER TABLE public.products 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'approved',
ADD COLUMN IF NOT EXISTS pdf_source TEXT,
ADD COLUMN IF NOT EXISTS extracted_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS approved_by TEXT,
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

-- Create index on status for faster queries
CREATE INDEX IF NOT EXISTS idx_products_status ON public.products(status);

-- Create index on extracted_at for sorting
CREATE INDEX IF NOT EXISTS idx_products_extracted_at ON public.products(extracted_at);

-- Update column comments
COMMENT ON COLUMN public.products.status IS 'Product status: pending, approved, or rejected';
COMMENT ON COLUMN public.products.pdf_source IS 'Source PDF filename if extracted from PDF';
COMMENT ON COLUMN public.products.extracted_at IS 'Timestamp when product was extracted from PDF';
COMMENT ON COLUMN public.products.approved_by IS 'Admin who approved the product';
COMMENT ON COLUMN public.products.approved_at IS 'Timestamp when product was approved';
COMMENT ON COLUMN public.products.rejection_reason IS 'Reason for rejection if product was rejected';

-- Add constraint to ensure status is valid
ALTER TABLE public.products 
ADD CONSTRAINT check_status 
CHECK (status IN ('pending', 'approved', 'rejected'));

