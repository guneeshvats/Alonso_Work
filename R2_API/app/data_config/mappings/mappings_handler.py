import os
import json
from app.constants import MappingsHandlerTerms

class MappingsHandler:
    """
    Handles fetching of different mappings (table names, field mappings, etc.)
    from JSON files stored in the `data_config/mappings` directory.
    """

    def __init__(self):
        """
        Initializes the MappingsHandler, preloading mappings from JSON files 
        to avoid repeated file I/O operations.
        """
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) 
        self.mappings_dir = os.path.join(self.base_dir, MappingsHandlerTerms.DATA_CONFIG.value, MappingsHandlerTerms.MAPPINGS_ROOT.value)
        self.stat_mapping_dir = os.path.join(self.mappings_dir, MappingsHandlerTerms.STAT_MAPPING_FOLDER.value)  
        self.query_samples_dir = os.path.join(self.base_dir, MappingsHandlerTerms.DATA_CONFIG.value, MappingsHandlerTerms.QUERY_SAMPLES.value)  

        # Preload mappings
        self.table_mapping = self._load_json(MappingsHandlerTerms.TABLE_MAPPING.value)
        self.fields_mapping = self._load_json(MappingsHandlerTerms.FIELDS_MAPPING.value)
        self.filter_mappings = self._load_json(MappingsHandlerTerms.FILTER_MAPPINGS.value)
        self.position_mappings = self._load_json(MappingsHandlerTerms.POSITION_MAPPINGS.value)
        self.metadata_mappings = self._load_json(MappingsHandlerTerms.METADATA_MAPPINGS.value)

    def _load_json(self, file_name: str) -> dict:
        """
        Private method to load a JSON file from a given file path.

        Args:
            file_name (str): The name of the JSON file.

        Returns:
            dict: Parsed JSON data as a dictionary.

        Raises:
            RuntimeError: If the file is not found or cannot be loaded.
        """
        file_path = os.path.join(self.mappings_dir, file_name) 
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise RuntimeError(f"File not found: {file_path}")
        except json.JSONDecodeError:
            raise RuntimeError(f"Error parsing JSON in {file_path}. Ensure it contains valid JSON.")

    def get_table_name(self, sport_code: str, entity: str, stat_period: str) -> str:
        """
        Fetches the correct table name based on sport_code, entity, and stat_period.

        Args:
            sport_code (str): The sport identifier (e.g., "MFB").
            entity (str): The entity type (e.g., "player", "team").
            stat_period (str): The statistical period (e.g., "game", "season").

        Returns:
            str: The corresponding table name, or None if not found.
        """
        return self.table_mapping.get(sport_code, {}).get(entity, {}).get(stat_period, None)


    def get_fields_for_query(self, sport_code : str, entity: str, stat_period: str, query_type: str) -> list:
        """
        Fetches the list of fields required for an SQL query based on entity, stat_period, and query_type.

        Args:
            entity (str): The entity type (e.g., "player", "team").
            stat_period (str): The statistical period (e.g., "game", "season").
            query_type (str): The type of query (e.g., "summary", "detailed").

        Returns:
            list: A list of field names, or an empty list if not found.
        """
        # return self.fields_mapping.get(entity, {}).get(stat_period, {}).get(query_type, [])
        return self.fields_mapping.get(sport_code, {}).get(entity, {}).get(stat_period, {}).get(query_type, [])


    def load_filter_mappings(self) -> dict:
        """
        Returns preloaded filter mappings.

        Returns:
            dict: A dictionary containing filter mappings.
        """
        return self.filter_mappings

    # def get_stat_mapping(self, sport_code: str, entity: str) -> dict:
    #     """
    #     Retrieves stat mappings for a given sport and entity (Player/Team).

    #     Args:
    #         sport_code (str): The sport identifier (e.g., "MFB", "MBB").
    #         entity (str): The entity type ("Player", "Team").

    #     Returns:
    #         dict: Stat mapping dictionary.
    #     """
    #     file_path = os.path.join(self.stat_mapping_dir, sport_code, f"{entity}.json")
    #     try:
    #         with open(file_path, "r", encoding="utf-8") as f:
    #             return json.load(f)
    #     except FileNotFoundError:
    #         return {}

    def get_stat_mapping(self, sport_code: str, entity: str) -> dict:
        """
        Retrieves stat mappings for a given sport and entity (Player/Team).

        Args:
            sport_code (str): The sport identifier (e.g., "MFB", "MBB").
            entity (str): The entity type ("Player", "Team").

        Returns:
            dict: Stat mapping dictionary with category field included.
        """
        file_path = os.path.join(self.stat_mapping_dir, sport_code, f"{entity}.json")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for entry in data:
                    # Ensure category and sub_category are properly set
                    entry["category"] = entry.get("category", "Unknown")
                    entry["sub_category"] = entry.get("sub_category", "")
                return data
        except FileNotFoundError:
            logger.error(f"Stat mapping file not found: {file_path}")
            return []
        except json.JSONDecodeError:
            logger.error(f"Error parsing JSON in {file_path}")
            return []


    def get_query_samples(self, sport_code: str, entity: str) -> list:
        """
        Retrieves example queries for a given sport code and entity.

        Args:
            sport_code (str): The sport identifier (e.g., "MFB", "MBB").
            entity (str): The entity type ("Player", "Team").

        Returns:
            list: A list of example queries.
        """
        file_path = os.path.join(self.query_samples_dir, sport_code, f"{entity.title()}.json")
        print(f"[DEBUG] Trying to load: {file_path}")

        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get("query_samples", [])
                elif isinstance(data, list):
                    return data  # ← fallback if file is a plain list
        except Exception as e:
            print(f"[ERROR] Failed to load query samples: {e}")
        return []
        
    def get_pos_mapping(self, sport_code: str) -> dict:
        """
        Retrieves position mappings for a given sport.

        Args:
            sport_code (str): The sport identifier (e.g., "MFB", "MBB").

        Returns:
            dict: Position mapping dictionary for the given sport.
        """
        return self.position_mappings.get(sport_code, {})
    
    def get_metadata_mapping(self) -> dict:
        """
        Returns metadata mappings.

        Returns:
            dict: A dictionary containing metadata mappings.
        """
        return self.metadata_mappings


