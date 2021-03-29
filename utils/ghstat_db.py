#!/usr/bin/python3
# Copyright: (c) 2021, Andrew Klychkov (@Andersson007) <aklychko@redhat.com>

from psycopg2.extensions import cursor as PgCursor

from utils.connection import (
    exec_in_db,
)

__VERSION__ = '0.1'


class GhStatDb():

    def __init__(self, cursor: PgCursor):
        self.cursor = cursor
        self.exec_in_db = exec_in_db
        self.repo = None

    def set_repo(self, repo: str):
        self.repo = repo

    def get_repos(self):
        res = self.exec_in_db(self.cursor, 'SELECT name FROM repos')
        return [r[0] for r in res]

    def get_branches(self):
        query = ('SELECT b.name FROM branches AS b '
                 'LEFT JOIN repos AS r ON r.id = b.repo_id '
                 'WHERE r.name = %s ORDER BY b.name')
        return self.exec_in_db(self.cursor, query, (self.repo,))

    def get_repo_release_stats(self) -> list:
        query = ('SELECT t.name AS "Release Version", c.ts AS "Release Date", '
                 'a.login AS "Release Manager", (SELECT NOW() - c.ts) AS "Time elapsed" '
                 'FROM tags AS t LEFT JOIN commits AS c ON c.id = t.commit_id '
                 'LEFT JOIN contributors AS a ON a.id = c.author_id '
                 'LEFT JOIN repos AS r ON r.id = t.repo_id '
                 'WHERE r.name = %s')

        return self.exec_in_db(self.cursor, query, (self.repo,))

    def get_global_release_stats(self, months_ago=0) -> dict:
        if not months_ago:
            query = ('SELECT r.name AS "Repo Name", max(c.ts) AS "Latest Release" '
                     'FROM tags AS t LEFT JOIN commits AS c ON c.id = t.commit_id '
                     'LEFT JOIN repos AS r ON r.id = t.repo_id '
                     'GROUP BY "Repo Name"')
        else:
            query = ('SELECT r.name AS "Repo Name", max(c.ts) AS "Latest Release" '
                     'FROM tags AS t LEFT JOIN commits AS c ON c.id = t.commit_id '
                     'LEFT JOIN repos AS r ON r.id = t.repo_id '
                     'GROUP BY "Repo Name" HAVING max(c.ts) < '
                     '(SELECT now() - \'%s month\'::interval)' % months_ago)

        res = self.exec_in_db(self.cursor, query)

        final_result = {}
        for row in res:
            final_result[row[0]] = {}
            final_result[row[0]]['tag'] = row[1]

        if not months_ago:
            query = ('SELECT r.name AS "Repo Name", max(c.ts) AS "Latest Commit" '
                     'FROM commits AS c LEFT JOIN repos AS r ON r.id = c.repo_id '
                     'GROUP BY "Repo Name"')
        else:
            query = ('SELECT r.name AS "Repo Name", max(c.ts) AS "Latest Commit" '
                     'FROM commits AS c LEFT JOIN repos AS r ON r.id = c.repo_id '
                     'GROUP BY "Repo Name" HAVING max(c.ts) < '
                     '(SELECT now() - \'%s month\'::interval)' % months_ago)

        res = self.exec_in_db(self.cursor, query)

        for row in res:
            print(row)
            if row[0] not in final_result:
                continue

            final_result[row[0]]['commit'] = row[1]

        return final_result

    def get_contributors(self):
        query = ('SELECT a.login AS "Author", a.email AS "Email", '
                 'count(c.id) AS "Commit number", max(c.ts) AS "Last commit TS" '
                 'FROM commits AS c LEFT JOIN contributors AS a '
                 'ON a.id = c.author_id LEFT JOIN repos AS r '
                 'ON c.repo_id = r.id WHERE r.name = %s '
                 'GROUP BY c.author_id, a.login, a.email '
                 'ORDER BY "Commit number" DESC')

        return self.exec_in_db(self.cursor, query, (self.repo,))
