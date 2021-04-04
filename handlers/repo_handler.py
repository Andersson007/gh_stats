#!/usr/bin/python3

from psycopg2.extensions import cursor as PgCursor

from .abc_handler import Handler

from utils.connection import exec_in_db


class RepoHandler(Handler):
    def __init__(self, cursor: PgCursor):
        self.cursor = cursor
        self.exec_in_db = exec_in_db

    def get_repo_list(self) -> list:
        """Get a repo list from the database."""
        res = self.exec_in_db(self.cursor, 'SELECT name FROM repos')
        if res:
            return [elem[0] for elem in res]
        return []

    def add(self, repo_name: str):
        """Add a repo to our database."""
        query = 'INSERT INTO repos (name) VALUES (%s)'
        self.exec_in_db(self.cursor, query, (repo_name,), ret_all=False)

    def get_id(self, repo_name: str) -> int:
        """Get a repo ID from the database."""
        query = 'SELECT id FROM repos WHERE name = %s'
        res = self.exec_in_db(self.cursor, query, (repo_name,))
        if res:
            return res[0][0]
        return None
