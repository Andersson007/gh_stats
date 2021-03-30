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


def _exit(conn: connection, rc=0, msg=''):
    if msg == '':
        msg = 'bye'

    if rc == 0:
        if msg is not None:
            print(msg)

        sys.exit(0)


class InputHandler():
    def __init__(self, gcli: GStatCli, conn):
        self.gcli = gcli
        self.conn = conn

    def handle_input(self, user_input: str):
        if user_input in ('quit', 'exit'):
            _exit(self.conn)

        if user_input in ('?', 'help'):
            self.gcli.show_available_commands()

        elif user_input == 'ls':
            self.gcli.print_repos()

        elif user_input == 'c':
            if self.gcli.current_repo == 'root':
                print('repo is not chosen')
                return
            else:
                self.gcli.show_contributors()

        elif user_input and user_input[0] == 'r':
            months_ago = 0
            if len(user_input) > 2:
                tmp = user_input.split()
                if len(tmp) >= 2:
                    months_ago = int(tmp[1])

            if self.gcli.current_repo == 'root':
                self.gcli.show_global_release_stats(months_ago)
            else:
                self.gcli.show_repo_release_stats()

        elif user_input[:3] == 'use':
            current_repo = user_input.split()[1]

            if current_repo not in self.gcli.repo_set and current_repo != 'root':
                print('"%s" repo does not exist, please '
                      'run "ls" to see all availabe '
                      'repos and try again' % current_repo)
                return

            self.gcli.set_current_repo(current_repo)

        elif user_input == 'b':
            if self.gcli.current_repo != 'root':
                self.gcli.print_branches()
            else:
                print('repo is not set, run "use repo.name" to choose')

        elif user_input != '':
            print('unrecognized command')


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

        handler = InputHandler(gcli, conn)

        while True:
            user_input = input('%s> ' % gcli.current_repo)

            handler.handle_input(user_input.strip())

    except KeyboardInterrupt:
        _exit(conn)

    except EOFError:
        _exit(conn)

    _exit(conn)


if __name__ == '__main__':
    main()
