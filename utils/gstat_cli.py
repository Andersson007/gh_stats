#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

from tabulate import tabulate

from utils.ghstat_db import GhStatDb


class GStatCli():
    def __init__(self, ghstat_db: GhStatDb):
        self.ghstat_db = ghstat_db
        self.current_repo = 'root'
        self.repo_set = set(ghstat_db.get_repos())

    def set_repo_set(self, repo_set: set):
        self.repo_set = repo_set

    def set_current_repo(self, repo: str):
        self.current_repo = repo
        if repo != 'root':
            self.ghstat_db.set_repo(repo)
        else:
            self.ghstat_db.set_repo(None)

    def show_available_commands(self):
        COMMANDS = [
            ['ls', 'show repo list'],
            ['use REPONAME', 'select a repo'],
            ['r', 'show release stats'],
            ['c', 'show contributors'],
            ['b', 'print branches'],
            ['CTRL+D', 'exit'],
            ['exit / quit', 'exit'],
            ['? / help', 'show this message'],
        ]

        print(tabulate(COMMANDS, headers=['Command', 'Description'],
              tablefmt='psql'))

    def print_repos(self):
        cnt = 1
        repo_list = sorted(list(self.repo_set))
        for repo in repo_list:
            print('[%s] %s' % (cnt, repo))
            cnt += 1

    def print_branches(self):
        cnt = 1
        for branch in self.ghstat_db.get_branches():
            print('[%s] %s' % (cnt, branch[0]))
            cnt += 1

    def show_global_release_stats(self, months_ago=0):
        result = self.ghstat_db.get_global_release_stats(months_ago)

        output = []
        for repo in result:
            tag_date = result[repo]['tag'].strftime('%d-%m-%Y')

            if result[repo].get('commit'):
                commit_date = result[repo]['commit'].strftime('%d-%m-%Y')
            else:
                commit_date = None
            output.append([repo, tag_date, commit_date])

        print(tabulate(output, headers=['Repo', 'Tag', 'Commit'],
              tablefmt='psql'))

    def show_repo_release_stats(self):
        result = self.ghstat_db.get_repo_release_stats()

        # It's a bad way but otherwise tabulate fails later
        headers = [['Release version', 'Date', 'Engineer', 'Elapsed']]

        result = headers + result

        print(tabulate(result, headers='firstrow', tablefmt='psql'))

    def show_contributors(self):
        result = self.ghstat_db.get_contributors()

        headers = [['Author', 'Email', 'Commit number', 'Last commit TS']]

        result = headers + result

        print(tabulate(result, headers='firstrow', tablefmt='psql'))
