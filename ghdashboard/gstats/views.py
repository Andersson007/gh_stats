from django.shortcuts import render

from .models import Repos


def test_view(request):
    """Test view"""
    repo_list = sorted([repo.name for repo in Repos.objects.all() if repo.name != '.github'])

    repo_num = len(repo_list)

    context = {
        'repo_list': repo_list,
        'repo_num': repo_num,
    }

    return render(request, 'gstats/index.html', context)
