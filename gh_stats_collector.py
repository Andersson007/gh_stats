#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

from argparse import ArgumentParser

from github import (
    Github,
    Repository,
)

from utils.connection import connect_to_db

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

    # TODO: Add DB connection parameters
    #

    return parser.parse_args()


def extract_repos(cli_arg: str) -> list:
    return [repo.strip() for repo in cli_arg.split(',')]


def handle_tags(repo: Repository):
    # Get tags
    tags = repo.get_tags()

    if not tags:
        return

    # What we should store
    # For tag in tags:
    # tag.name
    # tag.commit.sha
    # tag.last_modified
    # tag.tarball_url
    # Not sure all here:
    # tag.commit.sha
    # tag.commit.last_modified
    # tag.commit.author.login if tag.commit.author is specified
    # tag.commit.committer.login if tag.commit.committer is specified


def main():
    # Get command-line arguments
    cli_args = get_cli_args()

    # Create github object and set access token
    gh = Github(cli_args.token)

    # Handle repos
    repos_needed = None
    if cli_args.repo:
        repos_needed = extract_repos(cli_args.repo)

    # Get orgs
    gh_org = gh.get_organization(cli_args.org)

    # Get repos and do main job
    for repo in gh_org.get_repos():

        # Skip what we don't need
        if repos_needed and repo.name not in repos_needed:
            continue

        # Handle tags
        handle_tags(repo)

        # DEBUG: Print
        print(repo.full_name)

    # Set repos
    # gh_org = g.get_repo(cli_args.org)

    # Get repo list

    # TODO: Remove this debug print after all
    #print(repo_list)


if __name__ == '__main__':
    main()
