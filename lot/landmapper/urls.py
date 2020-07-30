from django.urls import include, re_path, path
from landmapper.views import *

urlpatterns = [
    # What is difference between re_path and path?
    # re_path(r'',
        # home, name='landmapper-home'),
    path('', home, name="home"),
    path('/identify/', identify, name="identify"),
    # path('/report/', report, name="report"),
    re_path(r'^report/((?P<cache_id>\w+)/)?$', report, name='report'),
    path('get_taxlot_json/', get_taxlot_json, name='get taxlot json'),
]
