from django.http import HttpResponse

from .models import Repos


def test_view(request):
    """Test view"""
    query_result = [repo.name for repo in Repos.objects.all()]

    return HttpResponse(query_result)
