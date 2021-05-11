from operator import itemgetter

from django.shortcuts import render

from .models import Repos, Branches


def index(request):
    return render(request, 'gstats/index.html', {})


def repos(request):
    """Repo list view."""
    repos = Repos.objects.raw('SELECT id, name FROM repos')
    repo_list = sorted([repo.name for repo in repos])

    repo_num = len(repo_list)

    context = {
        'repo_list': repo_list,
        'repo_num': repo_num,
    }

    return render(request, 'gstats/repos.html', context)


def repos_and_branches(request):
    """Repos and their branches."""
    repos = Repos.objects.raw('SELECT id, name FROM repos')

    query = ('SELECT b.id, b.name FROM branches AS b '
             'LEFT JOIN repos AS r ON r.id = b.repo_id '
             'WHERE r.name = %s ORDER BY b.name')

    repos_and_branches = []
    for repo in repos:
        branches = Branches.objects.raw(query, (repo.name,))
        repos_and_branches.append([repo.name, [b.name for b in branches]])

    repos_and_branches.sort()
    repo_num = len(repos)

    context = {
        'repos_and_branches': repos_and_branches,
        'repo_num': repo_num,
    }

    return render(request, 'gstats/repos-branches.html', context)


def latest_releases(request):
    """Global releases info: latest release, latest commit."""
    query = ('SELECT r.id, r.name, max(c.ts) AS latest_tag '
             'FROM tags AS t LEFT JOIN commits AS c ON c.id = t.commit_id '
             'LEFT JOIN repos AS r ON r.id = t.repo_id '
             'GROUP BY r.id, r.name')

    repos = Repos.objects.raw(query)

    tmp_dict = {}

    for repo in repos:
        tmp_dict[repo.name] = {}
        tmp_dict[repo.name]['tag'] = repo.latest_tag

    query = ('SELECT r.id, r.name, max(c.ts) AS latest_commit '
             'FROM commits AS c LEFT JOIN repos AS r ON r.id = c.repo_id '
             'GROUP BY r.id, r.name')

    repos = Repos.objects.raw(query)

    for repo in repos:
        if repo.name not in tmp_dict:
            continue
        tmp_dict[repo.name]['commit'] = repo.latest_commit

    repo_tag_commit = []
    for key, val in tmp_dict.items():
        repo_tag_commit.append([key, [val['tag'], val['commit']]])

    repo_tag_commit.sort(key=itemgetter(1), reverse=True)

    context = {
        'latest_releases': repo_tag_commit,
    }

    return render(request, 'gstats/latest-releases.html', context)


def repo_display(request, repo_name):
    # TODO: move out to a separate function
    # Get release info
    query = ('SELECT t.id, t.name, c.ts, '
             'a.login AS "author", age(c.ts) AS "time_elapsed" '
             'FROM tags AS t LEFT JOIN commits AS c ON c.id = t.commit_id '
             'LEFT JOIN contributors AS a ON a.id = c.author_id '
             'LEFT JOIN repos AS r ON r.id = t.repo_id '
             'WHERE r.name = %s')

    tags = Repos.objects.raw(query, (repo_name,))

    ret_list = []
    for tag in tags:
        ret_list.append([tag.name, tag.ts, tag.author, tag.time_elapsed])

    # TODO: sort it in the SQL query
    ret_list.sort(reverse=True)

    # TODO: move out to a separate function
    # TODO: maybe the latest commit time?
    # Get branch info
    query = ('SELECT b.id, b.name FROM branches AS b '
             'LEFT JOIN repos AS r ON r.id = b.repo_id '
             'WHERE r.name = %s ORDER BY b.name')

    branches = Branches.objects.raw(query, (repo_name,))

    context = {
        'branches': branches,
        'repo_name': repo_name,
        'tag_list': ret_list,
    }

    return render(request, 'gstats/repo-display.html', context)
