#!/usr/bin/python3

from psycopg2.extensions import cursor as PgCursor

from .abc_handler import Handler
from .repo_handler import RepoHandler

from utils.connection import exec_in_db


class BranchHandler(Handler):
    def __init__(self, cursor: PgCursor):
        self.cursor = cursor
        self.exec_in_db = exec_in_db
        self.repo = RepoHandler(cursor)

    def get_repo_branches(self, repo_name: str) -> dict:
        repo_id = self.repo.get_id(repo_name)

        query = ('SELECT name, id FROM branches WHERE repo_id = %s')
        res = self.exec_in_db(self.cursor, query, (repo_id,))

        if not res:
            return None

        name_id_dict = {}
        for item in res:
            name_id_dict[item[0]] = item[1]

        return name_id_dict

    def remove(self, branch_id: int):
        query = ('DELETE FROM branches WHERE id = %s')
        self.exec_in_db(self.cursor, query, (branch_id,), ret_all=False)

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
