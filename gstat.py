#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

import sys

from argparse import ArgumentParser

from psycopg2.extensions import connection

from utils.connection import connect_to_db

__VERSION__ = '0.1'


def get_cli_args():
    """Get command-line arguments."""
    parser = ArgumentParser(description='.')

    # DB connection related parameters
    parser.add_argument('-d', '--database', dest='database', required=True,
                        help='Database name to connect to', metavar='DBNAME')

    parser.add_argument('-u', '--user', dest='user', required=True,
                        help='Database user to log in with', metavar='DBUSER')

    parser.add_argument('-p', '--password', dest='password', required=True,
                        help='Database password', metavar='DBPASS')

    return parser.parse_args()


def handle_user_input(user_input: str):
    print(user_input)


def _exit(conn: connection, rc=0, msg=''):
    if msg == '':
        msg = 'bye'

    if rc == 0:
        if msg is not None:
            print(msg)

        sys.exit(0)


def main():
    try:
        # Get command-line arguments
        cli_args = get_cli_args()

        # Connect to database
        conn, cursor = connect_to_db(database=cli_args.database,
                                     user=cli_args.user,
                                     password=cli_args.password,
                                     autocommit=False)

        while True:

            user_input = input('gstat> ')

            if user_input.strip() in ('quit', 'exit'):
                _exit(conn)

            handle_user_input(user_input)

    except KeyboardInterrupt:
        _exit(conn)

    except EOFError:
        _exit(conn)

    _exit(conn)


if __name__ == '__main__':
    main()
