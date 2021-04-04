#!/usr/bin/python3

from psycopg2.extensions import cursor as PgCursor

from .abc_handler import Handler

from utils.connection import exec_in_db


class ContributorHandler(Handler):
    def __init__(self, cursor: PgCursor):
        self.cursor = cursor
        self.exec_in_db = exec_in_db

    def get_id(self, login: str) -> int:
        """Get a contributor ID from the database."""
        query = 'SELECT id FROM contributors WHERE login = %s'
        res = self.exec_in_db(self.cursor, query, (login,))
        if res:
            return res[0][0]
        return None

    def add(self, login: str, name: str, email: str):
        query = ('INSERT INTO contributors (login, name, email) '
                 'VALUES (%s, %s, %s)')
        self.exec_in_db(self.cursor, query, (login, name, email),
                        ret_all=False)
