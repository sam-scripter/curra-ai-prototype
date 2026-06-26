-- This script runs exactly once: when the PostgreSQL Docker container
-- is first created and the data volume is empty.
-- 
-- Its only job is to enable the pgvector extension before SQLAlchemy
-- tries to create the tables. If pgvector isn't enabled, the
-- 'vector' column type in our chunks table will throw an error.

CREATE EXTENSION IF NOT EXISTS vector;