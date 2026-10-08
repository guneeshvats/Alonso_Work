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

    # def to_representation(self, instance):
    #     """
    #     Remove NULL or None fields dynamically.
    #     """
    #     representation = super().to_representation(instance)
    #     return {k: v for k, v in representation.items() if v is not None}



# class SearchOutputSerializer(serializers.Serializer):
#     def __init__(self, *args, **kwargs):
#         pg_adapter = PGSQLAdapter()
#         table_name = "player_game_statistics"  # Set dynamically
#         columns = pg_adapter.get_table_columns(table_name)

#         for column in columns:
#             self.fields[column] = serializers.CharField(required=False)

#         super().__init__(*args, **kwargs)

    # gPersonId = serializers.IntegerField(required=False)
    # POS = serializers.CharField(required=False)
    # CLASS = serializers.CharField(default="UNK")
    # RES = serializers.CharField(required=False)
    # PLAYER = serializers.CharField(default="Unknown")
    # teamCode = serializers.IntegerField()
    # TEAM = serializers.CharField()
    # opponentTeamCode = serializers.CharField(required=False)
    # OPP = serializers.CharField(required=False)
    # gCompetitionId = serializers.IntegerField(required=False)
    # SEASON = serializers.CharField(required=False)
    # gConferenceId = serializers.IntegerField(default=0)
    # CONF = serializers.CharField(default="Unknown")
    # gOpponentConferenceId = serializers.IntegerField(default=0)
    # OPP_CONF = serializers.CharField(default="Unknown")
    # gMatchId = serializers.IntegerField()
    # DATE = serializers.CharField()
    # stats = serializers.DictField(child=serializers.JSONField(), required=False)

# class SearchOutputPSQLSerializer(serializers.Serializer):
#     gpersonid = serializers.IntegerField()
#     POS = serializers.CharField(required=False)
#     CLASS = serializers.CharField(default="UNK")
#     RES = serializers.CharField(required=False)
#     PLAYER = serializers.CharField(default="Unknown")
#     teamcode = serializers.IntegerField()
#     TEAM = serializers.CharField()
#     opponentteamcode = serializers.CharField(required=False)
#     OPP = serializers.CharField(required=False)
#     gcompetitionid = serializers.IntegerField(required=False)
#     SEASON = serializers.CharField(required=False)
#     gconferenceid = serializers.IntegerField(default=0)
#     CONF = serializers.CharField(default="Unknown")
#     gopponentconferenceid = serializers.IntegerField(default=0)
#     OPP_CONF = serializers.CharField(default="Unknown")
#     gmatchid = serializers.IntegerField()
#     DATE = serializers.CharField()
#     stats = serializers.DictField(child=serializers.JSONField(), required=False)

#     def update(self, instance, validated_data):
#         """
#         Handle extra fields dynamically.
#         """
#         for key, value in validated_data.items():
#             setattr(instance, key, value)
#         instance.save()
#         return instance
    
#     def to_representation(self, instance):
#         """
#         Override to include extra fields dynamically and handle ObjectId.
#         """
#         # Get the base representation (defined fields)
#         representation = super().to_representation(instance)

#                 # Add a fallback to ensure 'stats' is always present in the output
#         if "stats" not in representation:
#             representation["stats"] = {}
        
#         # If the instance is a dictionary, handle it differently
#         if isinstance(instance, dict):
#             for key, value in instance.items():
#                 # Convert ObjectId fields to string
#                 if isinstance(value, ObjectId):
#                     representation[key] = str(value)
#                 elif isinstance(value, dict):
#                     # If value is another dictionary, handle nested ObjectIds
#                     representation[key] = {k: str(v) if isinstance(v, ObjectId) else v for k, v in value.items()}
#                 elif isinstance(value, list):
#                     # If value is a list, handle each item
#                     representation[key] = [str(v) if isinstance(v, ObjectId) else v for v in value]
#                 else:
#                     # Add any other fields to the representation
#                     if key not in representation and key not in self.fields:
#                         representation[key] = value
#         elif isinstance(instance, list):
#             # Serialize each item in the list
#             data = super().to_representation(instance)
#             return {
#                 "count": len(instance),
#                 "results": data
#             }
#         else:
#             # If the instance is a model object, check its __dict__ attributes
#             for field, value in instance.__dict__.items():
#                 if isinstance(value, ObjectId):
#                     representation[field] = str(value)
#                 else:
#                     if field not in representation and field not in self.fields:
#                         representation[field] = value
                    
#         return representation


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
