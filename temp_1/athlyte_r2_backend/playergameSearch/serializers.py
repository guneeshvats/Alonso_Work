from bson import ObjectId
from rest_framework import serializers
from .pgsql_adapter import PGSQLAdapter 

class NameSuggestionsInputSerializer(serializers.Serializer):
    SportCode = serializers.CharField(default="MFB")
    Entity = serializers.CharField(default="Player")
    Prefix = serializers.CharField(default="")

class NameSuggestionsOutputSerializer(serializers.Serializer):
    Suggestions = serializers.DictField(required=False)

class PeriodConfigInputSerializer(serializers.Serializer):
    SportCode = serializers.CharField(default="MFB")

class PeriodConfigOutputSerializer(serializers.Serializer):
    Game = serializers.DictField(child=serializers.CharField())
    Seasons = serializers.DictField(child=serializers.CharField())
    Career = serializers.DictField(child=serializers.CharField())


#### input serializer
class SearchInputSerializer(serializers.Serializer):
    UserId = serializers.CharField(default='xyz')
    SportCode = serializers.CharField(default="MFB")
    TeamCode = serializers.IntegerField(required=False)
    BasicQuery = serializers.CharField(required=False)
    Entity = serializers.CharField(default="Player")
    TimePeriod = serializers.CharField(default="Game")
    GamePeriod = serializers.CharField(default="All Quarters")
    PageNumber = serializers.IntegerField(default=1)
    PageSize = serializers.IntegerField(default=10)
    Filters = serializers.DictField(default={})
    SortBy = serializers.CharField(default="None")
    SortOrder = serializers.CharField(default="DESC")
    AQLOnly = serializers.BooleanField(default=False)


class SearchOutputSerializer(serializers.Serializer):
    def __init__(self, column_names=None, *args, **kwargs):
        """
        Dynamically create serializer fields based on SQL query result columns.
        If column_names is None, default to an empty list.
        """
        super().__init__(*args, **kwargs)  # Ensure parent init is called
        self.fields = {}  # Define an empty dictionary for fields

        column_names = column_names or []  # Ensure column_names is always a list

        for column in column_names:
            self.fields[column] = serializers.CharField(required=False)
    
    def to_representation(self, instance):
        """
        Remove NULL (None) and 0.0 values dynamically from the response.
        """
        representation = super().to_representation(instance)

        # Exclude keys where the value is None or 0.0
        filtered_representation = {k: v for k, v in representation.items() if v not in (None, 0.0)}

        return filtered_representation


class SearchOutputPSQLSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        """
        Dynamically create serializer fields based on table structure.
        """
        pg_adapter = PGSQLAdapter()
        table_name = "player_game_statistics"  # Change this dynamically based on query

        # Fetch table columns dynamically
        columns = pg_adapter.get_table_columns(table_name)

        # Define fields dynamically
        for column in columns:
            self.fields[column] = serializers.CharField(required=False)

        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        """
        Override to include extra fields dynamically.
        """
        representation = super().to_representation(instance)

        # Ensure 'stats' field is always included
        if "stats" not in representation:
            representation["stats"] = {}

        # Convert ObjectId fields to string (for MongoDB compatibility)
        for key, value in instance.items():
            if isinstance(value, ObjectId):
                representation[key] = str(value)
            elif isinstance(value, dict):
                representation[key] = {k: str(v) if isinstance(v, ObjectId) else v for k, v in value.items()}
            elif isinstance(value, list):
                representation[key] = [str(v) if isinstance(v, ObjectId) else v for v in value]

        return representation
