-- Migration 001: Add authentication support
-- Run against your Supabase PostgreSQL database

-- Add password_hash column to users table
ALTER TABLE users
ADD COLUMN password_hash text;

-- Note: existing users will have NULL password_hash.
-- They will need to sign up again or have their password set manually.
