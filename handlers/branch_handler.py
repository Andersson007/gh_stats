#!/usr/bin/python3

from psycopg2.extensions import cursor as PgCursor

from .abc_handler import Handler

from utils.connection import exec_in_db


class BranchHandler(Handler):
    def __init__(self, cursor: PgCursor):
        self.cursor = cursor
        self.exec_in_db = exec_in_db

    def get_id(self, branch_name: str, repo_id: int) -> int:
        """Get a branch ID from the database."""
        query = 'SELECT id FROM branches WHERE name = %s AND repo_id = %s'
        res = self.exec_in_db(self.cursor, query, (branch_name, repo_id,))
        if res:
            return res[0][0]
        return None

    def add(self, name: str, repo_id: int):
        query = ('INSERT INTO branches (name, repo_id) '
                 'VALUES (%s, %s)')
        self.exec_in_db(self.cursor, query, (name, repo_id), ret_all=False)
