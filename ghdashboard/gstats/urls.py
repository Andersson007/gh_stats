from django.urls import path, re_path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('latest-releases.html', views.latest_releases, name='latest-releases'),
    path('repos.html', views.repos, name='repos'),
    path('repo-display/<str:repo_name>', views.repo_display, name='repo-display'),
    path('repos-branches.html', views.repos_and_branches, name='repos-branches'),
    path('export_releases_csv/', views.export_releases_csv),
]
