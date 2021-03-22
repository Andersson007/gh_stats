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

    def get_repos(self):
        return self.exec_in_db(self.cursor, 'SELECT name FROM repos')
