-- To create a PostgreSQL database with tables to store collected data in

CREATE DATABASE gh_stats;
\c gh_stats

-- Create table to store repositories data
CREATE TABLE IF NOT EXISTS repos (id serial primary key, name text, full_name text);

-- Create table to store tags data and link it with repo table
CREATE TABLE IF NOT EXISTS tags (id serial primary key, name text, repo_id int, last_modified timestamp, tarball_url text);
ALTER TABLE tags ADD CONSTRAINT fk_repo_id FOREIGN KEY (repo_id) REFERENCES repos (id);
