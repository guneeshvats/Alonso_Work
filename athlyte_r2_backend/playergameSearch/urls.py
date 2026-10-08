from django.urls import path
from .views import *

urlpatterns = [
    path('search/', search_players_nl, name='search-players-nl'),
    # path('search_regex/', search_players_regex, name='search-players-regex'),
    path('stat_mapping/', get_stat_mapping, name='stat-mapping'),
    path('get_period_config/', get_period_config, name ='get-period-config' ),
    path('post_name_suggestions/', post_name_suggestions, name ='post-name-suggestions' ),

    path('search_nl/', search_players_nl, name='search-players-nl'),
    path('report/', report_issue, name='report_issue'),

]