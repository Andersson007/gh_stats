#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

import sys

from argparse import ArgumentParser, Namespace
from configparser import ConfigParser

from github import (
    Github,
    Repository,
)

from psycopg2.extensions import cursor as PgCursor

from utils.connection import (
    connect_to_db,
    exec_in_db,
)

__VERSION__ = '0.1'


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


def get_repos_from_db(cursor: PgCursor) -> list:
    """Get a repo list from the database."""
    res = exec_in_db(cursor, 'SELECT name FROM repos')

    if res:
        return [elem[0] for elem in res]
    return []


def add_repo_to_db(cursor: PgCursor, repo_name: str):
    """Add a repo to our database."""
    exec_in_db(cursor, 'INSERT INTO repos (name) VALUES (%s)', (repo_name,),
               ret_all=False)


def get_repo_id(cursor: PgCursor, repo_name: str) -> int:
    """Get a repo ID from the database."""
    res = exec_in_db(cursor, 'SELECT id FROM repos WHERE name = %s', (repo_name,))
    if res:
        return res[0][0]
    return None


def get_contributor_id(cursor: PgCursor, login: str) -> int:
    """Get a contributor ID from the database."""
    res = exec_in_db(cursor, 'SELECT id FROM contributors WHERE login = %s', (login,))
    if res:
        return res[0][0]
    return None


def get_commit_id(cursor: PgCursor, sha: str) -> int:
    """Get a commit ID from the database."""
    res = exec_in_db(cursor, 'SELECT id FROM commits WHERE sha = %s', (sha,))
    if res:
        return res[0][0]
    return None


def get_branch_id(cursor, branch_name: str, repo_id: int) -> int:
    """Get a branch ID from the database."""
    query = 'SELECT id FROM branches WHERE name = %s AND repo_id = %s'
    res = exec_in_db(cursor, query, (branch_name, repo_id,))
    if res:
        return res[0][0]
    return None


def get_tag_id(cursor: PgCursor, repo_id: int, tag_name: str) -> int:
    """Get a tag ID from the database."""
    query = ('SELECT id FROM tags WHERE repo_id = %s AND name = %s')
    res = exec_in_db(cursor, query, (repo_id, tag_name))

    if res:
        return res[0][0]
    return None


def add_tag_to_db(cursor: PgCursor, repo_id: int, tag_name: str,
                  tarball: bool, commit_id: int):
    query = ('INSERT INTO tags (repo_id, name, tarball, commit_id) '
             'VALUES (%s, %s, %s, %s)')
    args = (repo_id, tag_name, tarball, commit_id,)
    exec_in_db(cursor, query, args, ret_all=False)


def add_contributor_to_db(cursor: PgCursor, login: str, name: str, email: str):
    query = ('INSERT INTO contributors (login, name, email) '
             'VALUES (%s, %s, %s)')
    exec_in_db(cursor, query, (login, name, email), ret_all=False)


def add_commit_to_db(cursor: PgCursor, sha: str, contributor_id: int,
                     repo_id: int, commit_ts: str, branch_id: int):
    query = ('INSERT INTO commits (sha, author_id, repo_id, ts, branch_id) '
             'VALUES (%s, %s, %s, %s, %s)')
    args = (sha, contributor_id, repo_id, commit_ts, branch_id)
    exec_in_db(cursor, query, args, ret_all=False)


def add_branch_to_db(cursor: PgCursor, name: str, repo_id: int):
    query = ('INSERT INTO branches (name, repo_id) '
             'VALUES (%s, %s)')
    exec_in_db(cursor, query, (name, repo_id), ret_all=False)


def handle_commits(cursor: PgCursor, repo: Repository, branch_name: str, branches_only=False):

    repo_id = get_repo_id(cursor, repo.name)

    branch_id = get_branch_id(cursor, branch_name, repo_id)
    if branch_id is None:
        add_branch_to_db(cursor, branch_name, repo_id)
        branch_id = get_branch_id(cursor, branch_name, repo_id)

    if branches_only:
        return

    commits = repo.get_commits(sha=branch_name)

    for commit in commits:

        if commit and commit.author:
            contributor_id = get_contributor_id(cursor, commit.author.login)
        else:
            continue

        if contributor_id is None and commit.author:
            add_contributor_to_db(cursor, commit.author.login,
                                  commit.author.name,
                                  commit.raw_data['commit']['author']['email'])

        commit_id = get_commit_id(cursor, commit.sha)

        if commit_id is None:
            contributor_id = get_contributor_id(cursor, commit.author.login)

            commit_ts = commit.raw_data['commit']['committer']['date']

            add_commit_to_db(cursor, commit.sha,
                             contributor_id,
                             repo_id,
                             commit_ts,
                             branch_id)


def handle_tags(cursor: PgCursor, repo: Repository):
    tags = repo.get_tags()

    if not tags:
        return

    repo_id = get_repo_id(cursor, repo.name)

    for tag in tags:
        tag_id = get_tag_id(cursor, repo_id, tag.name)

        if tag_id is None:
            commit_id = get_commit_id(cursor, tag.commit.sha)

            if commit_id is None:
                pass

            if tag.tarball_url:
                tarball = True
            else:
                tarball = False

            add_tag_to_db(cursor, repo_id, tag.name,
                          tarball, commit_id)


def main():

    try:
        # TODO: not sure if it's worth implementing
        #if sys.stdin and len(sys.argv) == 1:
        # We should pass:
        # 1) what to do (like fetch data from GH and update the DB)
        # 2) with what (e.g. with a collection)
        # 3) connection params
        # if everything is correct
        # 4) set up a flag not to use get_cli_args()
        # but define it here

        # Get command-line arguments
        cli_args = get_cli_args()

        # If config is passed, get options from it
        if cli_args.config:
            cli_args = parse_config(cli_args)

        # Connect to database
        conn, cursor = connect_to_db(database=cli_args.database,
                                     user=cli_args.user,
                                     password=cli_args.password,
                                     autocommit=True)

        repos_in_db = get_repos_from_db(cursor)

        # Create github object and set access token
        gh = Github(cli_args.token)

        # Handle repos
        repos_needed = None
        if cli_args.repo:
            repos_needed = extract_repos(cli_args.repo)

        # Get orgs
        gh_org = gh.get_organization(cli_args.org)

        # Get repos from GH and do main job
        for repo in gh_org.get_repos():
            # Skip what we don't need
            if repos_needed and repo.name not in repos_needed:
                continue

            # If we don't have it now, add repo to DB
            if repo.name not in repos_in_db:
                add_repo_to_db(cursor, repo.name)

            issues = repo.get_issues()
            print(issues.totalCount)
            # TODO:
            #1. Create a table for issues and PRs

            for issue in issues:
                print()
                print('ID:', issue.id)
                print('NUMBER:', issue.number)
                print('RAW_DATA["html_url"]:', issue.raw_data['html_url'])
                print('USER.LOGIN:', issue.user.login)
                print('USER.NAME:', issue.user.name)
                print('STATE:', issue.state)
                print('TITLE:', issue.title)
                print('BODY:', issue.body)
                print('CREATED_AT:', issue.created_at)
                print('UPDATED_AT:', issue.updated_at)
                print('CLOSED_AT:', issue.closed_at)
                print('CLOSED_BY:', issue.closed_by)
                print('COMMENTS:', issue.comments)

                comments = issue.get_comments()
                for comment in comments:
                    print('COMMENT.CREATED_AT:', comment.created_at)
                    print('COMMENT.USER.LOGIN:', comment.user.login)
                    break

                print('LABELS:', issue.labels)
                print('LAST_MODIFIED:', issue.last_modified)
                break

            if cli_args.issues_only:
                continue


            # Get branches
            branches = repo.get_branches()
            for branch in branches:
                # Handle commits
                handle_commits(cursor, repo, branch.name,
                               branches_only=cli_args.branches_only)

            if cli_args.branches_only:
                continue

            # Handle tags
            handle_tags(cursor, repo)

    except KeyboardInterrupt:
        print(' Interrupted')
        sys.exit(0)

    # DB close connection
    conn.close()
    sys.exit(0)


if __name__ == '__main__':
    main()
