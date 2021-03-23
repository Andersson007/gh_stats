#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

import sys

from argparse import ArgumentParser

from psycopg2.extensions import connection

from utils.connection import connect_to_db
from utils.ghstat_db import GhStatDb

__VERSION__ = '0.1'

repo_set = set()
current_repo = 'root'


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
        'use REPONAME   -- select a repo',
        'CTRL+D         -- exit',
        'exit / quit    -- exit',
        '? / help       -- show this message',
    ]

    HEADER = ('Command | Description')

    print(HEADER)
    for command in COMMANDS:
        print('ls -- show repo list')


def print_repos(repo_set: set):
    cnt = 1
    repo_list = sorted(list(repo_set))
    for repo in repo_list:
        print('[%s] %s' % (cnt, repo))
        cnt += 1


def print_branches(ghstat_db: GhStatDb):
    cnt = 1
    for branch in ghstat_db.get_branches():
        print('[%s] %s' % (cnt, branch[0]))
        cnt += 1


def handle_user_input(ghstat_db: GhStatDb, repo_set: set, user_input: str):
    global current_repo

    if user_input in ('?', 'help'):
        show_available_commands()

    elif user_input == 'ls':
        print_repos(repo_set)

    elif user_input[:3] == 'use':
        current_repo = user_input.split()[1]
        if current_repo not in repo_set:
            print('%s repo does not exist, please '
                  'run "ls" to see all availabe '
                  'repos and try again' % current_repo)
            return

        ghstat_db.set_repo(current_repo)

    elif user_input == 'b':
        print_branches(ghstat_db)


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

        global repo_set
        repo_set = set(ghstat_db.get_repos())

        while True:

            user_input = input('%s> ' % current_repo)

            if user_input.strip() in ('quit', 'exit'):
                _exit(conn)

            handle_user_input(ghstat_db, repo_set, user_input)

    except KeyboardInterrupt:
        _exit(conn)

    except EOFError:
        _exit(conn)

    _exit(conn)


if __name__ == '__main__':
    main()
