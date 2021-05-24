#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

import sys

from datetime import datetime

from time import sleep

from github import Github

from handlers.branch_handler import BranchHandler
from handlers.commit_handler import CommitHandler
from handlers.issue_handler import IssueHandler
from handlers.repo_handler import RepoHandler
from handlers.tag_handler import TagHandler

from utils.connection import connect_to_db

from utils.gh_stats_collector_functions import (
    extract_repos,
    get_cli_args,
    parse_config,
)


def main():

    try:
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

        repo_handler = RepoHandler(cursor)

        repos_in_db = repo_handler.get_repo_list()

        # Create github object and set access token
        gh = Github(cli_args.token)

        # Handle repos
        repos_needed = None
        if cli_args.repo:
            repos_needed = extract_repos(cli_args.repo)

        repos_to_skip = None
        if cli_args.skip_repo:
            repos_to_skip = extract_repos(cli_args.skip_repo)

        # Get orgs
        gh_org = gh.get_organization(cli_args.org)

        # Init handlers
        tag_handler = TagHandler(cursor)
        commit_handler = CommitHandler(cursor)
        issue_handler = IssueHandler(cursor)

        repos = gh_org.get_repos()

        # Get repos from GH and do main job
        for repo in repos:
            # Skip what we don't need
            if repos_needed and repo.name not in repos_needed:
                continue

            if repos_to_skip and repo.name in repos_to_skip:
                continue

            # If we don't have it now, add repo to DB
            if repo.name not in repos_in_db:
                repo_handler.add(repo.name)

            print(repo.name, end=' ')
            start_time = datetime.now()

            if cli_args.repos_only:
                end_time = datetime.now()
                print('done, took %s' % str(end_time - start_time))
                continue

            # Handle issues
            issue_handler.handle(repo)

            if cli_args.issues_only:
                end_time = datetime.now()
                print('done, took %s' % str(end_time - start_time))
                continue

            # Get branches from GitHub
            branches = repo.get_branches()

            # Get branches from DB
            branch_handler = BranchHandler(cursor)
            branches_in_db = branch_handler.get_repo_branches(repo.name)

            # Remove irrelevant branches from DB
            for b_name, b_id in branches_in_db.items():
                if b_name not in branches:
                    branch_handler.remove(b_id)

            # Handle branches
            for branch in branches:
                # Handle commits
                commit_handler.handle(repo, branch.name,
                                      branches_only=cli_args.branches_only)

            if cli_args.branches_only:
                continue

            # Handle tags
            tag_handler.handle(repo)

            end_time = datetime.now()
            print('done, took %s' % str(end_time - start_time))

            if cli_args.pause:
                sleep(int(cli_args.pause))

    except KeyboardInterrupt:
        print(' Interrupted')
        sys.exit(0)

    # DB close connection
    conn.close()
    sys.exit(0)


if __name__ == '__main__':
    main()
