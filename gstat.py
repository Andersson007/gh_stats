#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

import sys

from argparse import ArgumentParser

from psycopg2.extensions import connection

from utils.connection import connect_to_db
from utils.ghstat_db import GhStatDb

__VERSION__ = '0.1'

repo_list = []


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


def show_available_commands():
    COMMANDS = [
        'ls             -- show repo list',
        'CTRL+D         -- exit',
        'exit / quit    -- exit',
        '? / help       -- show this message',
    ]

    HEADER = ('Command | Description')

    print(HEADER)
    for command in COMMANDS:
        print('ls -- show repo list')


def print_repos(ghstat_db: GhStatDb):
    cnt = 1
    for repo in ghstat_db.get_repos():
        print('[%s] %s' % (cnt, repo))
        cnt += 1


def handle_user_input(ghstat_db: GhStatDb, user_input: str):
    if user_input in ('?', 'help'):
        show_available_commands()

    elif user_input == 'ls':
        print_repos(ghstat_db)


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

        ghstat_db = GhStatDb(cursor)

        # 1) Get available repos
        # 2) Pass it to a global variable
        # 3) Set a default root, e.g. 'gstat'
        # 4) handle_user_input looks into repo list
        # 5) if there's the desired repo, will change the default path
        # 6) if no, print a message to repeate the input

        while True:

            user_input = input('gstat> ')

            if user_input.strip() in ('quit', 'exit'):
                _exit(conn)

            handle_user_input(ghstat_db, user_input)

    except KeyboardInterrupt:
        _exit(conn)

    except EOFError:
        _exit(conn)

    _exit(conn)


if __name__ == '__main__':
    main()
