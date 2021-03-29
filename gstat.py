#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

import sys

from argparse import ArgumentParser

from psycopg2.extensions import connection

from utils.connection import connect_to_db
from utils.ghstat_db import GhStatDb
from utils.gstat_cli import GStatCli


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


def handle_user_input(gcli: GStatCli, user_input: str):

    if user_input in ('?', 'help'):
        gcli.show_available_commands()

    elif user_input == 'ls':
        gcli.print_repos()

    elif user_input == 'c':
        if gcli.current_repo == 'root':
            print('repo is not chosen')
            return
        else:
            gcli.show_contributors()

    elif user_input and user_input[0] == 'r':
        months_ago = 0
        if len(user_input) > 2:
            tmp = user_input.split()
            if len(tmp) >= 2:
                months_ago = int(tmp[1])

        if gcli.current_repo == 'root':
            gcli.show_global_release_stats(months_ago)
        else:
            gcli.show_repo_release_stats()

    elif user_input[:3] == 'use':
        current_repo = user_input.split()[1]

        if current_repo not in gcli.repo_set and current_repo != 'root':
            print('"%s" repo does not exist, please '
                  'run "ls" to see all availabe '
                  'repos and try again' % current_repo)
            return

        gcli.set_current_repo(current_repo)

    elif user_input == 'b':
        if gcli.current_repo is not None:
            gcli.print_branches()
        else:
            print('repo is not set, run "use repo.name" to choose')

    elif user_input != '':
        print('unrecognized command')


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

        gcli = GStatCli(ghstat_db)

        while True:
            user_input = input('%s> ' % gcli.current_repo)

            if user_input.strip() in ('quit', 'exit'):
                _exit(conn)

            handle_user_input(gcli, user_input)

    except KeyboardInterrupt:
        _exit(conn)

    except EOFError:
        _exit(conn)

    _exit(conn)


if __name__ == '__main__':
    main()
