-- Add Stripe billing columns to organization table
ALTER TABLE organization ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
ALTER TABLE organization ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);
ALTER TABLE organization ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'trialing';
ALTER TABLE organization ADD COLUMN IF NOT EXISTS subscription_ends_at TIMESTAMP;
ALTER TABLE organization ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP;
