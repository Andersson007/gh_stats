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
