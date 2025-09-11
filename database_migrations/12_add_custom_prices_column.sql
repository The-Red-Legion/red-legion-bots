-- Add custom_prices column to payroll_sessions table for Step 2.5 custom pricing feature
-- This stores user-defined ore prices that override UEX market prices

ALTER TABLE payroll_sessions 
ADD COLUMN IF NOT EXISTS custom_prices JSONB DEFAULT '{}';

-- Create index for faster queries on custom_prices
CREATE INDEX IF NOT EXISTS idx_payroll_sessions_custom_prices 
ON payroll_sessions USING gin(custom_prices);

-- Add comment for documentation
COMMENT ON COLUMN payroll_sessions.custom_prices IS 'User-defined ore prices that override UEX market prices in Step 2.5 custom pricing';