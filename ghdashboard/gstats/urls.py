from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('repos.html', views.repos, name='repos'),
    path('repos-branches.html', views.repos_and_branches, name='repos-branches'),
]
