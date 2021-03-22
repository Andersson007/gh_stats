#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

import sys

from argparse import ArgumentParser

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

    # Access token
    parser.add_argument('-t', '--token', dest='token', required=True,
                        help='GitHub access token', metavar='TOKEN')

    # GH organization
    parser.add_argument('-o', '--org', dest='org', required=True,
                        help='GitHub organization name', metavar='ORG')

    # Get data from a certain repo / repos
    parser.add_argument('-r', '--repo', dest='repo', required=False,
                        help='GitHub repository name or comma-separated list of names',
                        metavar='REPO_NAME')

    # DB connection related parameters
    parser.add_argument('-d', '--database', dest='database', required=True,
                        help='Database name to connect to', metavar='DBNAME')

    parser.add_argument('-u', '--user', dest='user', required=True,
                        help='Database user to log in with', metavar='DBUSER')

    parser.add_argument('-p', '--password', dest='password', required=True,
                        help='Database password', metavar='DBPASS')

    return parser.parse_args()


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


def handle_commits(cursor: PgCursor, repo: Repository, branch_name: str):
    commits = repo.get_commits(sha=branch_name)

    repo_id = get_repo_id(cursor, repo.name)

    branch_id = get_branch_id(cursor, branch_name, repo_id)
    if branch_id is None:
        add_branch_to_db(cursor, branch_name, repo_id)
        branch_id = get_branch_id(cursor, branch_name, repo_id)

    for commit in commits:
        # print(commit.raw_data['commit']['committer']['name'])
        # print(commit.raw_data['commit']['committer']['email'])

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
        # Get command-line arguments
        cli_args = get_cli_args()

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

            # Get branches
            branches = repo.get_branches()
            for branch in branches:
                # Handle commits
                handle_commits(cursor, repo, branch.name)

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
