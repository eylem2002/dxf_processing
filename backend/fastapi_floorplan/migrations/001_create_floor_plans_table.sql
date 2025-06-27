-- 001_create_floor_plans_table.sql
-- Migration to create the 'floor_plans' table if it doesn’t already exist

CREATE TABLE IF NOT EXISTS floor_plans (
    id VARCHAR(64) NOT NULL,
    keyword VARCHAR(64) NULL,
    relative_path TEXT NULL,
    metadata JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

