-- Migration: Enhanced Loan System for /red-loans subcommands
-- Date: September 8, 2025  
-- Purpose: Support loan approval workflow, payment tracking, and reminders

-- Update existing loans table with approval workflow
DO $$
BEGIN
    -- Add approval workflow columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'status') THEN
        ALTER TABLE loans ADD COLUMN status VARCHAR(20) DEFAULT 'pending';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'requested_amount') THEN
        ALTER TABLE loans ADD COLUMN requested_amount DECIMAL(15,2);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'approved_amount') THEN
        ALTER TABLE loans ADD COLUMN approved_amount DECIMAL(15,2);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'term_days') THEN
        ALTER TABLE loans ADD COLUMN term_days INTEGER DEFAULT 30;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'interest_rate') THEN
        ALTER TABLE loans ADD COLUMN interest_rate DECIMAL(5,4) DEFAULT 0.05;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'total_due') THEN
        ALTER TABLE loans ADD COLUMN total_due DECIMAL(15,2);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'paid_amount') THEN
        ALTER TABLE loans ADD COLUMN paid_amount DECIMAL(15,2) DEFAULT 0.00;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'request_reason') THEN
        ALTER TABLE loans ADD COLUMN request_reason TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'requested_by_id') THEN
        ALTER TABLE loans ADD COLUMN requested_by_id VARCHAR(20);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'requested_by_name') THEN
        ALTER TABLE loans ADD COLUMN requested_by_name VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'approved_by_id') THEN
        ALTER TABLE loans ADD COLUMN approved_by_id VARCHAR(20);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'approved_by_name') THEN
        ALTER TABLE loans ADD COLUMN approved_by_name VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'approval_notes') THEN
        ALTER TABLE loans ADD COLUMN approval_notes TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'denial_reason') THEN
        ALTER TABLE loans ADD COLUMN denial_reason TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'request_date') THEN
        ALTER TABLE loans ADD COLUMN request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'approval_date') THEN
        ALTER TABLE loans ADD COLUMN approval_date TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'due_date') THEN
        ALTER TABLE loans ADD COLUMN due_date TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'loans' AND column_name = 'next_reminder_date') THEN
        ALTER TABLE loans ADD COLUMN next_reminder_date TIMESTAMP;
    END IF;
END $$;

-- Loan payment history table
CREATE TABLE IF NOT EXISTS loan_payments (
    payment_id SERIAL PRIMARY KEY,
    loan_id INTEGER REFERENCES loans(loan_id) ON DELETE CASCADE,
    payer_id VARCHAR(20),
    payer_name VARCHAR(100),
    payment_amount DECIMAL(15,2) NOT NULL CHECK (payment_amount > 0),
    payment_type VARCHAR(20) DEFAULT 'payment' CHECK (payment_type IN ('payment', 'adjustment', 'penalty', 'forgiveness')),
    payment_method VARCHAR(50) DEFAULT 'manual',
    payment_notes TEXT,
    remaining_balance DECIMAL(15,2),
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recorded_by_id VARCHAR(20),
    recorded_by_name VARCHAR(100)
);

-- Loan reminder history table
CREATE TABLE IF NOT EXISTS loan_reminders (
    reminder_id SERIAL PRIMARY KEY,
    loan_id INTEGER REFERENCES loans(loan_id) ON DELETE CASCADE,
    reminder_type VARCHAR(20) DEFAULT 'payment_due' CHECK (reminder_type IN ('payment_due', 'overdue', 'final_notice')),
    days_before_due INTEGER,
    reminder_sent BOOLEAN DEFAULT FALSE,
    sent_date TIMESTAMP,
    recipient_id VARCHAR(20),
    recipient_name VARCHAR(100),
    message_content TEXT,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Loan settings table for configuration
CREATE TABLE IF NOT EXISTS loan_settings (
    setting_id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) REFERENCES guilds(guild_id),
    max_loan_amount DECIMAL(15,2) DEFAULT 1000000,
    default_interest_rate DECIMAL(5,4) DEFAULT 0.05,
    min_term_days INTEGER DEFAULT 7,
    max_term_days INTEGER DEFAULT 90,
    require_approval BOOLEAN DEFAULT TRUE,
    auto_reminders_enabled BOOLEAN DEFAULT TRUE,
    reminder_days_before JSON DEFAULT '[7, 3, 1]',  -- Days before due date to send reminders
    finance_officer_role_id VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id)
);

-- Indexes for loan operations
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);
CREATE INDEX IF NOT EXISTS idx_loans_requested_by ON loans(requested_by_id);
CREATE INDEX IF NOT EXISTS idx_loans_approved_by ON loans(approved_by_id);
CREATE INDEX IF NOT EXISTS idx_loans_due_date ON loans(due_date);
CREATE INDEX IF NOT EXISTS idx_loans_guild_status ON loans(guild_id, status);
CREATE INDEX IF NOT EXISTS idx_loans_next_reminder ON loans(next_reminder_date);

CREATE INDEX IF NOT EXISTS idx_loan_payments_loan ON loan_payments(loan_id);
CREATE INDEX IF NOT EXISTS idx_loan_payments_payer ON loan_payments(payer_id);
CREATE INDEX IF NOT EXISTS idx_loan_payments_date ON loan_payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_loan_payments_guild ON loan_payments(guild_id);

CREATE INDEX IF NOT EXISTS idx_loan_reminders_loan ON loan_reminders(loan_id);
CREATE INDEX IF NOT EXISTS idx_loan_reminders_type ON loan_reminders(reminder_type);
CREATE INDEX IF NOT EXISTS idx_loan_reminders_sent ON loan_reminders(reminder_sent);
CREATE INDEX IF NOT EXISTS idx_loan_reminders_guild ON loan_reminders(guild_id);

-- Add enhanced status constraint
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints 
                   WHERE constraint_name = 'chk_loan_status') THEN
        ALTER TABLE loans 
        ADD CONSTRAINT chk_loan_status 
        CHECK (status IN ('pending', 'approved', 'denied', 'active', 'overdue', 'paid', 'defaulted'));
    END IF;
END $$;

-- Create views for loan management
CREATE OR REPLACE VIEW active_loans AS
SELECT 
    l.loan_id,
    l.guild_id,
    l.requested_by_name,
    l.requested_amount,
    l.approved_amount,
    l.total_due,
    l.paid_amount,
    (l.total_due - l.paid_amount) as remaining_balance,
    l.interest_rate,
    l.term_days,
    l.status,
    l.due_date,
    l.next_reminder_date,
    l.request_date,
    l.approval_date,
    CASE 
        WHEN l.due_date < CURRENT_TIMESTAMP AND l.status = 'active' THEN 'overdue'
        ELSE l.status
    END as computed_status,
    CASE 
        WHEN l.due_date IS NOT NULL THEN EXTRACT(days FROM (l.due_date - CURRENT_TIMESTAMP))
        ELSE NULL
    END as days_until_due
FROM loans l
WHERE l.status IN ('pending', 'approved', 'active', 'overdue');

CREATE OR REPLACE VIEW loan_summary_by_user AS
SELECT 
    l.requested_by_id,
    l.requested_by_name,
    l.guild_id,
    COUNT(*) as total_loans,
    COUNT(*) FILTER (WHERE l.status = 'pending') as pending_loans,
    COUNT(*) FILTER (WHERE l.status IN ('active', 'approved')) as active_loans,
    COUNT(*) FILTER (WHERE l.status = 'overdue') as overdue_loans,
    COUNT(*) FILTER (WHERE l.status = 'paid') as paid_loans,
    COALESCE(SUM(l.approved_amount) FILTER (WHERE l.status IN ('active', 'approved', 'overdue')), 0) as total_borrowed,
    COALESCE(SUM(l.paid_amount), 0) as total_paid,
    COALESCE(SUM(l.total_due - l.paid_amount) FILTER (WHERE l.status IN ('active', 'approved', 'overdue')), 0) as total_outstanding
FROM loans l
GROUP BY l.requested_by_id, l.requested_by_name, l.guild_id;

-- Insert default loan settings for existing guilds
INSERT INTO loan_settings (guild_id, max_loan_amount, default_interest_rate, require_approval, auto_reminders_enabled)
SELECT DISTINCT guild_id, 1000000, 0.05, true, true
FROM guilds
ON CONFLICT (guild_id) DO NOTHING;