#!/usr/bin/python3

from github import Repository

from psycopg2.extensions import cursor as PgCursor

from .abc_handler import Handler

from .commit_handler import CommitHandler

from utils.connection import exec_in_db
from utils.gh_stats_collector_functions import get_repo_id


class TagHandler(Handler):
    def __init__(self, cursor: PgCursor):
        self.cursor = cursor
        self.exec_in_db = exec_in_db
        self.repo = None
        self.repo_id = 0
        self.tags = None
        self.commit_handler = CommitHandler(cursor)

    def handle(self, repo: Repository):
        if not self.__init_attrs(repo):
            # Return False when there are no tags.
            # Just return in this case
            return

        self.__handle_tags()

    def __handle_tags(self):
        for tag in self.tags:
            tag_id = self.get_id(tag.name)

            if tag_id is None:
                #TODO: replace get_repo_id with a proper
                # clasee later
                commit_id = self.commit_handler.get_id(tag.commit.sha)

                if commit_id is None:
                    pass

                if tag.tarball_url:
                    tarball = True
                else:
                    tarball = False

                self.add(tag.name, tarball, commit_id)

    def __init_attrs(self, repo: Repository):
        self.repo = repo
        self.repo_id = 0

        self.tags = self.repo.get_tags()
        if not self.tags:
            # If there are no tags
            return False

        #TODO: replace get_repo_id with a proper
        # clasee later
        self.repo_id = get_repo_id(self.cursor, self.repo.name)

        return True

    def add(self, tag_name: str, tarball: bool, commit_id: int):
        query = ('INSERT INTO tags (repo_id, name, tarball, commit_id) '
                 'VALUES (%s, %s, %s, %s)')
        args = (self.repo_id, tag_name, tarball, commit_id,)
        self.exec_in_db(self.cursor, query, args, ret_all=False)

    def get_id(self, tag_name: str) -> int:
        """Get a tag ID from the database."""
        query = ('SELECT id FROM tags WHERE repo_id = %s AND name = %s')
        res = self.exec_in_db(self.cursor, query, (self.repo_id, tag_name))
        if res:
            return res[0][0]
        return None
