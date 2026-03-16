-- 1. Create a custom ENUM type for strict Role-Based Access Control
CREATE TYPE user_role AS ENUM ('admin', 'analyst');

-- 2. Users Table
-- Stores the core identity. Passwords MUST be hashed (e.g., using bcrypt).
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role user_role NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Refresh Tokens Table (For Sliding Sessions)
-- This tracks the long-lived tokens securely. If an analyst goes offline 
-- for 31 minutes, we mark their token as revoked here.
CREATE TABLE refresh_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_string VARCHAR(512) UNIQUE NOT NULL,
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    
    -- An index to quickly look up a token when the frontend requests a refresh
    CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_refresh_token_string ON refresh_tokens(token_string);
CREATE INDEX idx_refresh_token_user ON refresh_tokens(user_id);

-- 4. Audit Table (Optional but highly recommended for SOAR)
-- Tracks when users log in or fail to log in.
CREATE TABLE auth_audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_attempted VARCHAR(255) NOT NULL,
    attempt_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    status VARCHAR(50) NOT NULL, -- 'SUCCESS', 'FAILED_PASSWORD', 'LOCKED'
    user_agent TEXT
);