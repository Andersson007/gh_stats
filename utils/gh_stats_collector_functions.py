#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

import sys

from argparse import ArgumentParser, Namespace
from configparser import ConfigParser


def get_cli_args():
    """Get command-line arguments."""
    parser = ArgumentParser(description='.')

    # Config
    parser.add_argument('-c', '--config', dest='config',
                        help='Path to config file', metavar='PATH')

    # Access token
    parser.add_argument('-t', '--token', dest='token',
                        help='GitHub access token', metavar='TOKEN')

    # GH organization
    parser.add_argument('-o', '--org', dest='org',
                        help='GitHub organization name', metavar='ORG')

    # Get data from a certain repo / repos
    parser.add_argument('-r', '--repo', dest='repo',
                        help='GitHub repository name or comma-separated list of names',
                        metavar='REPO_NAME')

    skip_msg = ('Repository name or comma-separated list of names to skip '
                'handling (GitHub API will not be called)')
    parser.add_argument('--skip', dest='skip_repo',
                        help=skip_msg, metavar='REPO_NAME')

    # Update the repo list only in DB
    parser.add_argument('--repos-only', dest='repos_only',
                        help='Fetch and update repo list only',
                        action='store_true')

    # Get data from a certain repo / repos
    parser.add_argument('-b', '--branches-only', dest='branches_only',
                        help='Fetch branches only',
                        action='store_true')

    parser.add_argument('-i', '--issues-only', dest='issues_only',
                        help='Fetch issues only',
                        action='store_true')

    # DB connection related parameters
    parser.add_argument('-d', '--database', dest='database',
                        help='Database name to connect to', metavar='DBNAME')

    parser.add_argument('-u', '--user', dest='user',
                        help='Database user to log in with', metavar='DBUSER')

    parser.add_argument('-p', '--password', dest='password',
                        help='Database password', metavar='DBPASS')

    args = parser.parse_args()

    if not args.config:
        if not all((args.database, args.user, args.password, args.token, args.org,)):
            print('-c or all of -t, -d, -u, -p, -o arguments must be specified')
            sys.exit(1)

    return args


def parse_config(cli_args: Namespace):
    """Parse a config file.

    If an option is already in cli_args, ignore the one from config.
    """
    config = ConfigParser()
    config.read(cli_args.config)

    connection_present = False
    github_present = False

    for section in config.sections():

        if section == 'connection':

            connection_present = True

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

        elif section == 'github':

            github_present = True

            if not cli_args.token:

                if config['github'].get('token'):
                    cli_args.token = config['github']['token']
                else:
                    print('-t command-line argument or "token" '
                          'setting in config must be specified')
                    sys.exit(1)

            if not cli_args.org:

                if config['github'].get('organization'):
                    cli_args.org = config['github']['organization']
                else:
                    print('-o command-line argument or "organization" '
                          'setting in config must be specified')
                    sys.exit(1)

    if not all((connection_present, github_present,)):
        print('both [connection] and [github] sections '
              'in config file must be specified')
        sys.exit(1)

    return cli_args


def extract_repos(cli_arg: str) -> list:
    """Make a list from a passed-via-cli string."""
    return [repo.strip() for repo in cli_arg.split(',')]
