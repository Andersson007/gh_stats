#!/usr/bin/python3

from psycopg2 import connect
from psycopg2.extensions import cursor


def connect_to_db(database: str, user: str, password: str) -> (connect, cursor):
    """Create a connection object and cursor.
    Returns a tuple (connection object, cursor)
    """
    # For simplicity, now it accepts only
    # a login user and login password implying
    # that you run PostgreSQL locally.
    # Be sure, you configure access properly

    try:
        conn = connect(host='localhost',
                       database=database,
                       user=user,
                       password=password)
    except Exception as e:
        print('Unable to connect to the database: %s' % e)

    return conn, conn.cursor()
