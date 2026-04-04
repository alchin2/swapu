
-- Let Supabase auto-generate UUIDs

INSERT INTO users (email, name, max_cash_amt, max_cash_pct) VALUES
  ('alice@test.com', 'Alice', 50.00, 20.00),
  ('bob@test.com', 'Bob', 100.00, 30.00);

-- Get the user IDs
-- Then use them to create items and deals below
-- (Easier to do this via the Python seed script instead: src/seed.py)