#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

import sys

from github import Github

from handlers.issue_handler import IssueHandler
from handlers.commit_handler import CommitHandler
from handlers.tag_handler import TagHandler
from handlers.repo_handler import RepoHandler

from utils.connection import connect_to_db

from utils.gh_stats_collector_functions import (
    extract_repos,
    get_cli_args,
    parse_config,
)


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

        repo_handler = RepoHandler(cursor)

        repos_in_db = repo_handler.get_repo_list()

        # Create github object and set access token
        gh = Github(cli_args.token)

        # Handle repos
        repos_needed = None
        if cli_args.repo:
            repos_needed = extract_repos(cli_args.repo)

        # Get orgs
        gh_org = gh.get_organization(cli_args.org)

        # Init handlers
        tag_handler = TagHandler(cursor)
        commit_handler = CommitHandler(cursor)
        issue_handler = IssueHandler(cursor)

        # Get repos from GH and do main job
        for repo in gh_org.get_repos():
            # Skip what we don't need
            if repos_needed and repo.name not in repos_needed:
                continue

            # If we don't have it now, add repo to DB
            if repo.name not in repos_in_db:
                repo_handler.add(repo.name)

            # Handle issues
            issue_handler.handle(repo)
            # TODO:
            # 1. [DONE] Create a table for issues and PRs
            # 2. Create IssueHandler class
            # 3. Initialize it
            # 4. In the loop below, issue.add(issue) or issue_handler.handle(issues)
            # 4.1. If the issue already exists, update it if needed
            # 5. Create table for comments
            # 6. Write CommentHandler class
            # 7. Put comments into the table referencing to issues table via a foreign key

            if cli_args.issues_only:
                continue

            # Get branches
            branches = repo.get_branches()
            for branch in branches:
                # Handle commits
                commit_handler.handle(repo, branch.name,
                                      branches_only=cli_args.branches_only)

            if cli_args.branches_only:
                continue

            # Handle tags
            tag_handler.handle(repo)

    except KeyboardInterrupt:
        print(' Interrupted')
        sys.exit(0)

    # DB close connection
    conn.close()
    sys.exit(0)


if __name__ == '__main__':
    main()
