#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

import sys

from argparse import (
    ArgumentParser,
    Namespace,
)
from configparser import ConfigParser

from psycopg2.extensions import connection

from utils.connection import connect_to_db
from utils.ghstat_db import GhStatDb
from utils.gstat_cli import GStatCli


def get_cli_args():
    """Get command-line arguments."""
    parser = ArgumentParser(description='.')

    # Config
    parser.add_argument('-c', '--config', dest='config',
                        help='Path to config file', metavar='PATH')

    # DB connection related parameters
    parser.add_argument('-d', '--database', dest='database',
                        help='Database name to connect to', metavar='DBNAME')

    parser.add_argument('-u', '--user', dest='user',
                        help='Database user to log in with', metavar='DBUSER')

    parser.add_argument('-p', '--password', dest='password',
                        help='Database password', metavar='DBPASS')

    args = parser.parse_args()

    if not args.config:
        if not all((args.database, args.user, args.password)):
            print('-c or all of -d, -u, -p arguments must be specified')
            sys.exit(1)

    return args


def parse_config(cli_args: Namespace):
    """Parse a config file.

    If an option is already in cli_args, ignore the one from config.
    """
    config = ConfigParser()
    config.read(cli_args.config)

    for section in config.sections():

        if section == 'connection':

            if not cli_args.database:

                if config['connection'].get('database'):
                    cli_args.database = config['connection']['database']
                else:
                    print('-d command-line argument or "database" '
                          'setting in config must be specified')
                    sys.exit(1)

            if not cli_args.user:

                if config['connection'].get('user'):
                    cli_args.user = config['connection']['user']
                else:
                    print('-u command-line argument or "user" '
                          'setting in config must be specified')
                    sys.exit(1)

            if not cli_args.password:

                if config['connection'].get('password'):
                    cli_args.password = config['connection']['password']
                else:
                    print('-p command-line argument or "password" '
                          'setting in config must be specified')
                    sys.exit(1)

    return cli_args


def _exit(conn: connection, rc=0, msg=''):
    if msg == '':
        msg = 'bye'

    if rc == 0:
        conn.close()

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

        # Get not passed arguments from config
        if cli_args.config:
            cli_args = parse_config(cli_args)

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
