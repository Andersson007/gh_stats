-- To create a PostgreSQL database with tables to store collected data in

CREATE DATABASE gh_stats;
\c gh_stats

-- Create a table to store contributors
CREATE TABLE IF NOT EXISTS contributors (id BIGSERIAL PRIMARY KEY, login TEXT NOT NULL, name TEXT, email TEXT);
ALTER TABLE contributors ADD CONSTRAINT uniq_contributors_login UNIQUE (login);

-- Create a table to store repositories data
CREATE TABLE IF NOT EXISTS repos (id SERIAL PRIMARY KEY, name TEXT);
ALTER TABLE repos ADD CONSTRAINT uniq_repos_name UNIQUE (name);

-- Create a table to store branches
CREATE TABLE IF NOT EXISTS branches (id BIGSERIAL PRIMARY KEY, name TEXT, repo_id INT);
ALTER TABLE branches ADD CONSTRAINT fk_repo_id FOREIGN KEY (repo_id) REFERENCES repos (id);

-- Create a table to store commits
CREATE TABLE IF NOT EXISTS commits (id BIGSERIAL PRIMARY KEY, sha TEXT, author_id BIGINT, repo_id INT, ts TIMESTAMP, branch_id INT);
ALTER TABLE commits ADD CONSTRAINT uniq_commits_sha UNIQUE (sha);
ALTER TABLE commits ADD CONSTRAINT fk_author_id FOREIGN KEY (author_id) REFERENCES contributors (id);
ALTER TABLE commits ADD CONSTRAINT fk_repo_id FOREIGN KEY (repo_id) REFERENCES repos (id);
ALTER TABLE commits ADD CONSTRAINT fk_branch_id FOREIGN KEY (branch_id) REFERENCES branches (id);

-- Create a table to store tags data and link it with repo table
CREATE TABLE IF NOT EXISTS tags (id SERIAL PRIMARY KEY, name TEXT, repo_id INT, tarball BOOLEAN, commit_id BIGINT);
ALTER TABLE tags ADD CONSTRAINT fk_repo_id FOREIGN KEY (repo_id) REFERENCES repos (id);
ALTER TABLE tags ADD CONSTRAINT fk_commit_id FOREIGN KEY (commit_id) REFERENCES commits (id);

-- SELECT * FROM repos LIMIT 5;

-- SELECT * FROM tags LIMIT 5;

-- SELECT r.name AS "repo name", t.name AS "tag name", c.ts AS "date", t.tarball AS released FROM tags AS t LEFT JOIN repos AS r ON t.repo_id = r.id LEFT JOIN commits AS c ON t.commit_id = c.id WHERE r.name = 'community.digitalocean';

-- SELECT a.login AS author, a.email, count(c.id) AS commit_number, max(c.st) AS last_commit_time FROM commits AS c LEFT JOIN contributors AS a ON a.id = c.author_id LEFT JOIN repos AS r ON c.repo_id = r.id WHERE r.name = 'community.mysql' GROUP BY c.author_id, a.login, a.email ORDER BY commit_number DESC;

-- SELECT r.name AS repo, b.name AS branch, a.login AS author, c.ts AS ts_created FROM commits AS c LEFT JOIN repos AS r ON r.id = c.repo_id LEFT JOIN contributors AS a ON c.author_id = a.id LEFT JOIN branches AS b ON b.id = c.branch_id WHERE r.name = 'community.network' AND b.name = 'main' ORDER BY ts_created DESC LIMIT 10;

-- SELECT t.name AS "Release Version", c.ts AS "Release Date", a.login AS "Release Manager" FROM tags AS t LEFT JOIN commits AS c ON c.id = t.commit_id LEFT JOIN contributors AS a ON a.id = c.author_id LEFT JOIN repos AS r ON r.id = t.repo_id WHERE r.name = 'community.mysql'

-- SELECT t.name AS "Release Version", c.ts AS "Release Date", a.login AS "Release Manager", (SELECT NOW() - c.ts) AS "How long ago" FROM tags AS t LEFT JOIN commits AS c ON c.id = t.commit_id LEFT JOIN contributors AS a ON a.id = c.author_id LEFT JOIN repos AS r ON r.id = t.repo_id WHERE r.name = 'ansible.posix';
