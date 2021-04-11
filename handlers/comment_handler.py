#!/usr/bin/python3

from github.PaginatedList import PaginatedList
from psycopg2.extensions import cursor as PgCursor

from .abc_handler import Handler
from .contributor_handler import ContributorHandler

from utils.connection import exec_in_db


class CommentHandler(Handler):
    def __init__(self, cursor: PgCursor):
        self.cursor = cursor
        self.exec_in_db = exec_in_db
        self.contributor = ContributorHandler(cursor)

    def add(self, id_: int, repo_id: int, issue_id: int, author_id: int, ts_created: str):
        """Add a repo to our database."""
        query = ('INSERT INTO comments (id, repo_id, issue_id, author_id, ts_created) '
                 'VALUES (%s, %s, %s, %s, %s)')
        args = (id_, repo_id, issue_id, author_id, ts_created)
        self.exec_in_db(self.cursor, query, args, ret_all=False)

    def get_id(self, id_: int) -> int:
        """Check if a comment ID exists in the database."""
        query = 'SELECT id FROM comments WHERE id = %s'
        res = self.exec_in_db(self.cursor, query, (id_,))
        if res:
            return res[0][0]
        return None

    def handle(self, repo_id: int, issue_id: int, comments: PaginatedList):
        """Handle comments."""
        for comment in comments:

            comment_id = self.get_id(comment.id)
            if comment_id is not None:
                # When the comment already
                # exists in the database
                continue

            author_id = self.contributor.get_id(comment.user.login)
            if author_id is None:
                self.contributor.add(comment.user.login,
                                     comment.user.name,
                                     comment.user.raw_data['email'])
                author_id = self.contributor.get_id(comment.user.login)

            self.add(comment.id, repo_id, issue_id, author_id, comment.created_at)
