def parse_query_postgres(query, stat_mapping):
    """
    Parses the query string and returns a PostgreSQL-compatible WHERE clause and query parameters.

    Args:
        query (str): The user input query.
        stat_mapping (dict): Mapping of AthlyteLabel to GeniusLabel.

    Returns:
        tuple: (SQL WHERE clause string, list of query parameters, list of mapped stats)

    Raises:
        ValidationError: If the query format is invalid.
    """
    print("Converted query regex:", query)

    # Validate number of connectives
    connective = validate_connectives(query)

    # Regex pattern for multiple conditions
    condition_pattern = r'\"(.*?)\"\s*(=|!=|>|<|>=|<=)\s*(\d+(\.\d+)?|\".*?\")'
    multiple_condition_pattern = (
        r'\"(.*?)\"\s*(=|!=|>|<|>=|<=)\s*(\d+(\.\d+)?|\".*?\")'  # condition (stat operator value)
        r'(\s*(AND|OR)\s*'  # optional connective (AND/OR)
        r'\"(.*?)\"\s*(=|!=|>|<|>=|<=)\s*(\d+(\.\d+)?|\".*?\")'  # another condition
        r')*'  # This allows the pattern to repeat (for multiple AND/OR connected conditions)
    )

    # Validate input query matches the multiple condition pattern
    if not re.fullmatch(multiple_condition_pattern, query):
        raise ValidationError("Invalid query format. Ensure the query matches the required condition pattern.")

    # Extract all conditions from the query
    conditions = re.findall(condition_pattern, query)
    mapped_stats = []

    if not conditions:
        raise ValidationError("No valid conditions found in query.")

    # Loop over conditions and process them
    query_conditions = []  # SQL WHERE conditions
    query_values = []  # Parameters for the SQL query

    for condition in conditions:
        stat, op, value = condition[0].lower(), condition[1], condition[2]

        # Normalize stat mapping to lowercase
        stat_mapping = {k.lower(): v for k, v in stat_mapping.items()}
        validate_stats_in_mapping([stat], stat_mapping)

        # Map stat and create condition
        stat_mapped = stat_mapping.get(stat)
        if not stat_mapped:
            raise ValidationError(f"Stat '{stat}' not found in stat mapping.")
        mapped_stats.append(stat_mapped)

        # Convert the operator to SQL format
        sql_operator = op if op != "!=" else "<>"

        # Handle string values (ensure proper escaping)
        if value.startswith('"') and value.endswith('"'):
            value = value.strip('"')  # Remove surrounding quotes

        query_conditions.append(f"{stat_mapped} {sql_operator} {value}")
        query_values.append(value)

    # Combine conditions using the correct connective
    if connective == "AND":
        where_clause = " AND ".join(query_conditions)
    elif connective == "OR":
        where_clause = " OR ".join(query_conditions)
    else:
        where_clause = query_conditions[0]  # Single condition case

    print(where_clause, query_values, mapped_stats)
    return where_clause, query_values, mapped_stats


@swagger_auto_schema(
    method='post',
    operation_summary="Search Players with Regex Filters",
    operation_description=(
            "This API allows users to search for player data based on a combination of filters such as sport code, "
            "entity type, and time/game periods. The `BasicQuery` parameter accepts logical conditions (e.g., "
            "'\"Stat\" >= 10 AND \"Stat\" < 20') which are dynamically mapped to the appropriate database fields. "
            "Example: {\"BasicQuery\": \"\\\\\"Reception yards\\\\\" > 50 AND \\\\\"Rushing yards net\\\\\" >= 50\"}"
    ),
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "BasicQuery": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Logical query to filter player data.",
                example="\"Reception yards\" > 50 AND \"Rushing yards net\" >= 50"
            ),

            "SportCode": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Sport code to filter players (e.g., 'MFB').",
                example="MFB"
            ),
            "TeamCode": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="TeamCode to filter teams.",
                example="31"
            ),
            "Entity": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Entity type to search (e.g., 'Player').",
                example="Player"
            ),
            "TimePeriod": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Game, Season or Career.",
                example="Game"
            ),
            "GamePeriod": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Period within game. Eg. All Quarters, First Quarter, Overtime",
                example="All Quarters"
            ),
            "PageNumber": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="PageNumber for Pagination.",
                example=1
            ),
            "PageSize": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="PageSize for Pagination.",
                example=10
            ),
        },
        required=["BasicQuery"],
    ),
    responses={
        200: openapi.Response(
            description="List of players matching the search criteria.",
            schema=SearchOutputSerializer(many=True),
            examples={
                "application/json": [
                    {
                        "gPersonId": "12345",
                        "PLAYER": "John Doe",
                        "POS": "Quarterback",
                        "TEAM": "Team A",
                        "SEASON": 2024,
                        "Reception yards": 100,
                        "Rushing yards net": 50,
                    }
                ]
            },
        ),

        400: openapi.Response(
            description="Invalid request format or validation error.",
        ),
        500: openapi.Response(
            description="Server error while processing the request.",
        ),
    },
    tags=["Player Search"],
)
@api_view(['POST'])
def search_players_regex(request):
    # Validate input using the serializer
    # Using serializers for now as we have mock data stored in Python script
    # print("Here - in search-regex function")
    serializer = SearchInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    # print(validated_data)

    user_id = validated_data.get('UserId')
    sport_code = validated_data.get('SportCode')
    team_code = validated_data.get('TeamCode')
    basic_query = validated_data.get('BasicQuery')
    entity = validated_data.get('Entity')
    time_period = validated_data.get('TimePeriod')
    game_period = validated_data.get('GamePeriod')
    page_number = validated_data.get('PageNumber')
    page_size = validated_data.get('PageSize')
    filters = validated_data.get('Filters', {})
    sort_by = validated_data.get('SortBy', 'playerName')
    sort_order = validated_data.get('SortOrder', 'asc')

    game_period_mapping = get_game_period_mapping()

    # Parse the query
    query_filter = {}
    if basic_query:
        try:
            stat_mapping_query = {"entity": entity.lower()}
            stat_mapping_ag = {entry['AthlyteLabel']: entry['GeniusLabel'] for entry in
                               statmapping_collection.find(stat_mapping_query)}
            query_filter, mapped_stats = parse_query(basic_query, stat_mapping_ag)
            print(basic_query, query_filter)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    else:
        mapped_stats = [
        ]

    try:
        additional_query_filters = {}

        filter_mappings = {
            'TEAM': 'teamName',
            'OPP': 'opponentTeamName',
            'PLAYER': ('playerName', {'$regex': None, '$options': 'i'}),
            'POS': 'position',
            'CLASS': 'playerClass',
            'RES': 'gameResult',
            'SEASON': 'academicSeason',
            'CONF': 'teamConferenceName',
            'OPP_CONF': 'opponentConferenceName'
        }

        if team_code:
            additional_query_filters['teamCode'] = team_code
        if game_period and game_period in game_period_mapping:
            additional_query_filters.update(game_period_mapping[game_period])

        for filter_key, db_key in filter_mappings.items():
            if filter_key in filters:
                filter_value = filters[filter_key]

                if isinstance(db_key, tuple):  # Handle regex-based filtering
                    db_field, query_template = db_key
                    if isinstance(filter_value, list):
                        additional_query_filters["$or"] = [{db_field: {"$regex": v, "$options": "i"}} for v in
                                                           filter_value]
                    else:
                        query_template['$regex'] = filter_value
                        additional_query_filters[db_field] = query_template
                else:
                    if isinstance(filter_value, list):
                        additional_query_filters[db_key] = {"$in": filter_value}
                    else:
                        additional_query_filters[db_key] = filter_value

        if 'START DATE' in filters:
            try:
                start_date = datetime.strptime(filters['START DATE'], "%m/%d/%Y")
                end_date = datetime.strptime(filters.get('END DATE', datetime.today().strftime("%m/%d/%Y")), "%m/%d/%Y")
                additional_query_filters['$expr'] = {
                    "$and": [
                        {"$gte": [{"$dateFromString": {"dateString": "$actualDate", "format": "%m/%d/%Y"}},
                                  start_date]},
                        {"$lte": [{"$dateFromString": {"dateString": "$actualDate", "format": "%m/%d/%Y"}}, end_date]}
                    ]
                }
            except ValueError:
                return Response({"error": "Invalid date format."}, status=status.HTTP_400_BAD_REQUEST)

        # Sorting
        stat_mapping_rev = {entry['AthlyteShortLabel']: entry['GeniusLabel'] for entry in
                            statmapping_collection.find(stat_mapping_query)}
        sort_direction = ASCENDING if sort_order.lower() == 'asc' else DESCENDING
        sort_stage = None
        if not sort_by:
            sort_by = []
        elif sort_by == 'DATE':
            # sort_by = [({"$dateFromString": {"dateString": "$actualDate", "format": "%m/%d/%Y"}}, sort_direction)]
            # Use an aggregation pipeline to convert the date before sorting
            sort_stage = [
                {"$addFields": {
                    "parsedDate": {"$dateFromString": {"dateString": "$actualDate", "format": "%m/%d/%Y"}}}},
                {"$sort": {"parsedDate": sort_direction}}
            ]
        elif sort_by == 'SEASON':
            sort_by = [("season", sort_direction)]
        elif sort_by == 'PLAYER':
            sort_by = [("playerName", sort_direction)]
        elif sort_by in stat_mapping_rev.keys():
            sort_by = [(stat_mapping_rev[sort_by], sort_direction)]
        elif sort_by in filter_mappings.keys():
            sort_by = [(filter_mappings[sort_by], sort_direction)]
        else:
            sort_by = [(sort_by, sort_direction)]

            # Wrap the existing query_filter with $and if it's not empty
        if query_filter:
            query_filter = {"$and": [query_filter, additional_query_filters]}
        else:
            query_filter = additional_query_filters or {}

        print("q:", query_filter)

        if page_number < 1 or page_size <= 0:
            raise ValueError("Invalid pagination parameters: page_number and page_size must be positive.")
        skip_value = (page_number - 1) * page_size

        count = playergame_collection.count_documents(query_filter)

        if skip_value > count:
            raise ValueError(
                f"Invalid pagination parameters: The requested page number ({page_number}) exceeds the total number of available pages.")

        fixed_projection = {
            "gPersonId": 1,
            "position": 1,
            "playerClass": 1,
            "gameResult": 1,
            "playerName": 1,
            "teamCode": 1,
            "teamName": 1,
            "opponentTeamCode": 1,
            "opponentTeamName": 1,
            "gCompetitionId": 1,
            "academicSeason": 1,
            "gConferenceId": 1,
            "teamConferenceName": 1,
            "gOpponentConferenceId": 1,
            "opponentConferenceName": 1,
            "gMatchId": 1,
            "actualDate": 1,
            "_id": 0
        }
        dynamic_projection = {stat: 1 for stat in mapped_stats}

        # Combine fixed projection with dynamic projection
        projection = {**fixed_projection, **dynamic_projection}
        try:
            if sort_by:
                if sort_by == 'DATE':
                    pipeline = []
                    if query_filter:
                        pipeline.append({"$match": query_filter})  # Apply filters
                    pipeline.extend(sort_stage)  # Add sorting stages
                    pipeline.append({"$skip": skip_value})
                    pipeline.append({"$limit": page_size})
                    pipeline.append({"$project": projection})  # Apply projection
                    print("pipeline: ", pipeline)
                    result = playergame_collection.aggregate(pipeline)
                else:
                    result = playergame_collection.find(query_filter, projection).sort(sort_by).skip(skip_value).limit(
                        page_size)
            else:
                result = playergame_collection.find(query_filter, projection).skip(skip_value).limit(page_size)
        except Exception as e:
            return Response({"error in running mongo query: ": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        result_list = list(result)

        # Convert GeniusLabel to AthlyteLabel

        # Get all stat mappings from the statmapping collection

        stat_mapping = {entry['GeniusLabel']: entry['AthlyteShortLabel'] for entry in
                        statmapping_collection.find(stat_mapping_query)}
        try:
            result_list = format_output(result_list, stat_mapping)
        except Exception as e:
            return Response({"error in formatting op: ": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        positions, player_classes, teams = get_pos_class_team_values()
        # print(positions, player_classes)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    output_serializer = SearchOutputSerializer(result_list, many=True)

    return Response({
        "count": count,
        "results": output_serializer.data,
        "positions": positions,
        "playerClasses": player_classes,
        "teams": teams
    })


def parse_query(query, stat_mapping):
    """
    Parses the query string and returns a MongoDB-compatible filter for multiple conditions.

    Args:
        query (str): The user input query.
        stat_mapping (dict): Mapping of AthlyteLabel to GeniusLabel.

    Returns:
        dict: MongoDB query filter.

    Raises:
        ValidationError: If the query format is invalid.
    """
    print("in converted data - regex", query)
    # Validate number of connectives
    connective = validate_connectives(query)

    # Regex pattern for multiple conditions
    condition_pattern = r'\"(.*?)\"\s*(=|!=|>|<|>=|<=)\s*(\d+(\.\d+)?|\".*?\")'
    multiple_condition_pattern = (
        r'\"(.*?)\"\s*(=|!=|>|<|>=|<=)\s*(\d+(\.\d+)?|\".*?\")'  # condition (stat operator value)
        r'(\s*(AND|OR)\s*'  # optional connective (AND/OR)
        r'\"(.*?)\"\s*(=|!=|>|<|>=|<=)\s*(\d+(\.\d+)?|\".*?\")'  # another condition
        r')*'  # This allows the pattern to repeat (for multiple AND/OR connected conditions)
    )

    # Validate input query matches the multiple condition pattern
    if not re.fullmatch(multiple_condition_pattern, query):
        raise ValidationError("Invalid query format. Ensure the query matches the required condition pattern.")

    # Extract all conditions from the query
    conditions = re.findall(condition_pattern, query)
    mapped_stats = []

    if not conditions:
        raise ValidationError("No valid conditions found in query.")

    # Loop over conditions and process them
    query_filter = []  # to hold the conditions for AND/OR logic
    for condition in conditions:
        stat, op, value = condition[0].lower(), condition[1], condition[2]

        # Validate stats

        stat_mapping = {stat.lower(): stat_value for stat, stat_value in stat_mapping.items()}
        validate_stats_in_mapping([stat], stat_mapping)

        # Map stat and create condition
        stat_mapped = stat_mapping.get(stat)
        if not stat_mapped:
            raise ValidationError(f"Stat '{stat}' not found in stat mapping.")
        mapped_stats.append(stat_mapped)

        query_filter.append(create_condition(stat_mapped, op, value.strip('"')))

    # If the connective is AND, combine conditions directly
    if connective == "AND":
        # return {**query_filter[0], **query_filter[1]} if len(query_filter) == 2 else {"$and": query_filter}
        return {"$and": query_filter}, mapped_stats

    # If the connective is OR, wrap all conditions in an $or clause
    if connective == "OR":
        return {"$or": query_filter}, mapped_stats

    return query_filter[0], mapped_stats  # Return all conditions if no AND/OR found




def validate_stats_in_mapping(stats, stat_mapping):
    """
    Validates that all stats in the query are present in the stat mapping.
    """
    #print(stat_mapping, stats)
    missing_stats = [stat for stat in stats if stat not in stat_mapping]
    if missing_stats:
        raise ValidationError(f"The following stats are missing in the mapping: {', '.join(missing_stats)}")


def validate_connectives(query):
    """
    Validates the query to ensure:
    - A maximum of 4 'AND's or 4 'OR's are allowed.
    - No mixing of 'AND' and 'OR'.
    """
    connectives = re.findall(r'\b(AND|OR)\b', query.upper())

    if not connectives:
        return None

    # Check if the query contains both 'AND' and 'OR'
    if "AND" in connectives and "OR" in connectives:
        raise ValidationError("Query cannot mix 'AND' and 'OR' connectives.")

    # Ensure the count of a single connective (AND or OR) does not exceed 4
    if len(connectives) > 3:
        raise ValidationError(f"Query must not contain more than 4 '{connectives[0]}' connectives.")

    return connectives[0]



def create_condition(field, operator, value):
    """
    Helper function to create MongoDB conditions.
    """
    def parse_value(val):
        try:
            # First, attempt to convert to an integer
            return int(val)
        except ValueError:
            try:
                # If int conversion fails, try float
                return float(val)
            except ValueError:
                # If all conversions fail, return as is (likely a string)
                return val

    # Parse the value to ensure proper numeric types when applicable
    parsed_value = parse_value(value)
    try:
        if operator == "=":
            return {field: parsed_value}
        elif operator == "!=":
            return {field: {"$ne": parsed_value}}
        elif operator == ">":
            return {field: {"$gt": parsed_value}}
        elif operator == "<":
            return {field: {"$lt": parsed_value}}
        elif operator == ">=":
            return {field: {"$gte": parsed_value}}
        elif operator == "<=":
            return {field: {"$lte": parsed_value}}
        else:
            raise ValidationError(f"Invalid operator: {operator}")
    except ValueError:
        raise ValidationError(f"Invalid value '{value}' for operator '{operator}'.")


def format_output_psql(result_list, stat_mapping):
    # Replace the GeniusLabel with AthlyteLabel in the result
    map_col_names = {
        "position": "POS",
        "playerclass": "CLASS",
        "gameresult": "RES",
        "playername": "PLAYER",
        "teamname": "TEAM",
        "opponentteamname": "OPP",
        "academicseason": "SEASON",
        "teamconferencename": "CONF",
        "opponentconferencename": "OPP_CONF",
        "actualdate": "DATE",
    }
    for doc in result_list:

        stats_dict = {}

        # Create a copy of the original doc items to avoid modifying during iteration
        new_doc = doc.copy()
        keys_to_delete = []

        for key, value in doc.items():
            if isinstance(key, str) and key in stat_mapping:
                # Replace GeniusLabel with AthlyteLabel
                new_key = stat_mapping[key].upper()
                stats_dict[new_key] = value
                keys_to_delete.append(key)
            if isinstance(key, str) and key in map_col_names:
                # Replace GeniusLabel with AthlyteLabel
                new_key = map_col_names[key]
                new_doc[new_key] = value
                keys_to_delete.append(key)
        new_doc["stats"] = stats_dict

        # Update the original document with the new keys and values
        for key in keys_to_delete:
            new_doc.pop(key, None)

        doc.clear()
        doc.update(new_doc)

    return result_list

