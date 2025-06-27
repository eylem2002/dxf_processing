-- 001_create_project_dxf_links_table.sql
-- Migration to create the 'project_dxf_links' join table for linking projects to floor plans

CREATE TABLE IF NOT EXISTS project_dxf_links (
    project_id VARCHAR(100) NOT NULL,
    floor_plan_id VARCHAR(100) NOT NULL,
    PRIMARY KEY (project_id, floor_plan_id),
    CONSTRAINT fk_floor_plan
        FOREIGN KEY (floor_plan_id)
        REFERENCES floor_plans(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
