#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

from psycopg2.extensions import cursor as PgCursor

from utils.connection import (
    exec_in_db,
)

__VERSION__ = '0.1'


class GhStatDb():

    def __init__(self, cursor: PgCursor):
        self.cursor = cursor
        self.exec_in_db = exec_in_db
        self.repo = None

    def set_repo(self, repo: str):
        self.repo = repo

    def get_repos(self):
        res = self.exec_in_db(self.cursor, 'SELECT name FROM repos')
        return [r[0] for r in res]

    def get_branches(self):
        query = ('SELECT b.name FROM branches AS b '
                 'LEFT JOIN repos AS r ON r.id = b.repo_id '
                 'WHERE r.name = %s ORDER BY b.name')
        return self.exec_in_db(self.cursor, query, (self.repo,))
