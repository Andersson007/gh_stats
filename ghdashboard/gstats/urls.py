from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('latest-releases.html', views.latest_releases, name='latest-releases'),
    path('repos.html', views.repos, name='repos'),
    path('repos-branches.html', views.repos_and_branches, name='repos-branches'),
]
