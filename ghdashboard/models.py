# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Branches(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    repo = models.ForeignKey('Repos', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'branches'


class Comments(models.Model):
    id = models.BigIntegerField(primary_key=True)
    repo = models.ForeignKey('Repos', models.DO_NOTHING, blank=True, null=True)
    issue = models.ForeignKey('Issues', models.DO_NOTHING, blank=True, null=True)
    author = models.ForeignKey('Contributors', models.DO_NOTHING, blank=True, null=True)
    ts_created = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'comments'


class Commits(models.Model):
    id = models.BigAutoField(primary_key=True)
    sha = models.TextField(unique=True, blank=True, null=True)
    author = models.ForeignKey('Contributors', models.DO_NOTHING, blank=True, null=True)
    repo = models.ForeignKey('Repos', models.DO_NOTHING, blank=True, null=True)
    ts = models.DateTimeField(blank=True, null=True)
    branch = models.ForeignKey(Branches, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'commits'


class Contributors(models.Model):
    id = models.BigAutoField(primary_key=True)
    login = models.TextField()
    name = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'contributors'


class Issues(models.Model):
    id = models.BigIntegerField(primary_key=True)
    repo = models.ForeignKey('Repos', models.DO_NOTHING, blank=True, null=True)
    number = models.IntegerField(blank=True, null=True)
    is_issue = models.BooleanField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    author = models.ForeignKey(Contributors, models.DO_NOTHING, blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    ts_created = models.DateTimeField(blank=True, null=True)
    ts_updated = models.DateTimeField(blank=True, null=True)
    ts_closed = models.DateTimeField(blank=True, null=True)
    comment_cnt = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'issues'


class Repos(models.Model):
    name = models.TextField(unique=True, blank=True, null=True)
    full_name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'repos'


class Tags(models.Model):
    name = models.TextField(blank=True, null=True)
    repo = models.ForeignKey(Repos, models.DO_NOTHING, blank=True, null=True)
    tarball = models.BooleanField(blank=True, null=True)
    commit = models.ForeignKey(Commits, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tags'
