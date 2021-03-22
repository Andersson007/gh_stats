#!/usr/bin/python3

import sys

from psycopg2 import connect
from psycopg2.extensions import cursor
from psycopg2.extras import DictCursor


def connect_to_db(database: str, user: str, password: str, autocommit=False) -> (connect, cursor):
    """Create a connection object and cursor.
    Returns a tuple (connection object, cursor).
    """
    # For simplicity, now it accepts only
    # a login user and login password implying
    # that you run PostgreSQL locally.
    # Be sure, you configure access properly

    conn = None
    try:
        conn = connect(host='localhost',
                       database=database,
                       user=user,
                       password=password)
    except Exception as e:
        print('Unable to connect to the database: %s' % e, file=sys.stderr)
        sys.exit(1)

    if autocommit:
        conn.set_session(autocommit=True)

    return conn, conn.cursor(cursor_factory=DictCursor)


def exec_in_db(curs: cursor, statement: str,
               args=(), ret_all=True) -> list:
    """Execute a statement in a database."""
    try:
        curs.execute(statement, args)

        if ret_all:
            return curs.fetchall()

    except Exception as e:
        print('Cannot execute statement: %s' % e, file=sys.stderr)
        sys.exit(1)

    return []
