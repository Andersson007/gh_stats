#!/usr/bin/python3

from github import Repository

from psycopg2.extensions import cursor as PgCursor

from .abc_handler import Handler
from .branch_handler import BranchHandler
from .contributor_handler import ContributorHandler
from .repo_handler import RepoHandler

from utils.connection import exec_in_db


class CommitHandler(Handler):
    def __init__(self, cursor: PgCursor):
        self.cursor = cursor
        self.exec_in_db = exec_in_db
        self.branch = BranchHandler(cursor)
        self.contributor = ContributorHandler(cursor)
        self.repo = RepoHandler(cursor)

    def get_id(self, sha: str) -> int:
        """Get a commit ID from the database."""
        query = 'SELECT id FROM commits WHERE sha = %s'
        res = self.exec_in_db(self.cursor, query, (sha,))
        if res:
            return res[0][0]
        return None

    def add(self, sha: str, contributor_id: int,
            repo_id: int, commit_ts: str, branch_id: int):
        """Add a commit to the database."""
        query = ('INSERT INTO commits (sha, author_id, repo_id, ts, branch_id) '
                 'VALUES (%s, %s, %s, %s, %s)')
        args = (sha, contributor_id, repo_id, commit_ts, branch_id)

        self.exec_in_db(self.cursor, query, args, ret_all=False)

    def handle(self, repo: Repository, branch_name: str, branches_only=False):
        repo_id = self.repo.get_id(repo.name)

        branch_id = self.branch.get_id(branch_name, repo_id)
        if branch_id is None:
            self.branch.add(branch_name, repo_id)
            branch_id = self.branch.get_id(branch_name, repo_id)

        if branches_only:
            return

        commits = repo.get_commits(sha=branch_name)

        for commit in commits:

            if commit and commit.author:
                contributor_id = self.contributor.get_id(commit.author.login)
            else:
                continue

            if contributor_id is None and commit.author:
                self.contributor.add(commit.author.login,
                                     commit.author.name,
                                     commit.raw_data['commit']['author']['email'])

            commit_id = self.get_id(commit.sha)

            if commit_id is None:
                contributor_id = self.contributor.get_id(commit.author.login)

                commit_ts = commit.raw_data['commit']['committer']['date']

                self.add(commit.sha, contributor_id, repo_id, commit_ts, branch_id)
