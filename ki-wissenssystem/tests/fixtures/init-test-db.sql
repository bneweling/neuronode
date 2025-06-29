-- ===================================================================
-- TEST DATABASE INITIALIZATION SCRIPT
-- Enterprise Test Environment Setup
-- ===================================================================

-- Create separate test databases
CREATE DATABASE test_ki_db;
CREATE DATABASE test_litellm_db;

-- Create test user with appropriate permissions
CREATE USER test_user WITH PASSWORD 'test_pass';

-- Grant permissions for test databases
GRANT ALL PRIVILEGES ON DATABASE test_ki_db TO test_user;
GRANT ALL PRIVILEGES ON DATABASE test_litellm_db TO test_user;

-- Connect to test_ki_db for initial setup
\c test_ki_db;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO test_user;

-- Create test data tables (if needed)
CREATE TABLE IF NOT EXISTS test_documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    content TEXT,
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS test_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert test users
INSERT INTO test_users (email, role) VALUES 
    ('test.internal@ki-system.com', 'internal_user'),
    ('admin@ki-system.com', 'proxy_admin'),
    ('viewer@ki-system.com', 'internal_user_viewer')
ON CONFLICT (email) DO NOTHING;

-- Connect to test_litellm_db for LiteLLM setup
\c test_litellm_db;

-- Grant permissions for LiteLLM
GRANT ALL ON SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO test_user;

-- LiteLLM will create its own tables automatically
-- This just ensures the database exists with proper permissions

-- Success message
SELECT 'Test databases initialized successfully' AS status; 