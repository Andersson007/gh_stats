#!/usr/bin/python3

from github import Repository
from github.Issue import Issue

from psycopg2.extensions import cursor as PgCursor

from .abc_handler import Handler
from .contributor_handler import ContributorHandler
from .repo_handler import RepoHandler

from utils.connection import exec_in_db


class IssueHandler(Handler):
    def __init__(self, cursor: PgCursor):
        self.cursor = cursor
        self.exec_in_db = exec_in_db
        self.contributor = ContributorHandler(cursor)
        self.repo = RepoHandler(cursor)
        self.contributor = ContributorHandler(cursor)

    def get_id(self, issue_id: int) -> int:
        """Get an issue ID from the database."""
        query = 'SELECT id FROM issues WHERE id = %s'
        res = self.exec_in_db(self.cursor, query, (issue_id,))
        if res:
            return res[0][0]
        return None

    def add(self, issue_id, repo_id, number, is_issue, state, author_id,
            title, ts_created, ts_updated, ts_closed, comment_cnt):
        """Add an issue to the database."""
        query = ('INSERT INTO issues (id, repo_id, number, is_issue, '
                 'state, author_id, title, ts_created, ts_updated, ts_closed, '
                 'comment_cnt) '
                 'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)')
        args = (issue_id, repo_id, number, is_issue, state, author_id,
                title, ts_created, ts_updated, ts_closed, comment_cnt)

        self.exec_in_db(self.cursor, query, args, ret_all=False)

    def update(self, issue):
        #TODO: complete
        # 1. Get columns that can be updated (in a dict form)
        # 2. Compater
        # 3. Update fields which needed
        cur_vals = self.__issue_get_mutable_cols(issue)

        cur_vals_set = set(list(cur_vals.values()))

        new_vals_set = set([issue.state, issue.title, issue.updated_at,
                           issue.closed_at, issue.comments])

        if cur_vals_set != new_vals_set:
            print(cur_vals_set)
            print(new_vals_set)


    def __issue_get_mutable_cols(self, issue: Issue):
        query = ('SELECT state, title, ts_updated, ts_closed, comment_cnt '
                 'FROM issues WHERE id = %s')
        res = self.exec_in_db(self.cursor, query, (issue.id,))
        res = [dict(row) for row in res]
        return res[0]

    def handle(self, repo: Repository):

        issues = repo.get_issues(state='all')
        if issues is None:
            return

        repo_id = self.repo.get_id(repo.name)

        for issue in issues:

            author_id = self.contributor.get_id(issue.user.login)
            if author_id is None:
                self.contributor.add(issue.user.login,
                                     issue.user.name,
                                     issue.user.raw_data['email'])
                author_id = self.contributor.get_id(issue.user.login)

            issue_id = self.get_id(issue.id)
            if issue_id is not None:
                # When issue is already in the table, update it if needed
                self.update(issue)

            else:
                if 'issue' in issue.raw_data['html_url']:
                    is_issue = True
                else:
                    is_issue = False

                self.add(issue.id, repo_id, issue.number, is_issue, issue.state,
                         author_id, issue.title, issue.created_at, issue.updated_at,
                         issue.closed_at, issue.comments)
