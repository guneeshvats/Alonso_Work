import os
from app.constants import Qualifiers

class SQLTemplateLoader:
    """
    A utility class that manages loading and caching of SQL template files.
    
    This class provides functionality to load SQL templates from a specified directory,
    cache them in memory, and retrieve them on demand. It supports lazy loading of
    templates that weren't loaded during initialization.
    
    Attributes:
        template_dir (str): Directory path containing SQL template files. Defaults to 'app/sql_templates'.
        templates (dict): Cache storing loaded SQL templates, mapping query_type to template content.
    """

    def __init__(self, template_dir="app/sql_templates"):
        """
        Initialize the SQLTemplateLoader with a template directory.
        
        Args:
            template_dir (str): Path to directory containing SQL template files.
                              Defaults to 'app/sql_templates'.
                              
        On initialization, loads all SQL files from the template directory into memory.
        """
        self.template_dir = template_dir
        self.templates = {}
        
        # Eagerly load all SQL templates during initialization for faster subsequent access
        for filename in os.listdir(self.template_dir):
            if filename.endswith('.sql'):
                query_type = filename[:-4]  # Strip .sql extension to get template type
                template_path = os.path.join(self.template_dir, filename)
                with open(template_path, "r") as file:
                    self.templates[query_type] = file.read()

    def load_template(self, query_type):
        """
        Load and return an SQL template for the specified query type.
        
        This method first checks the in-memory cache for the template. If not found,
        attempts to load it from the filesystem. Templates are cached after loading
        to improve performance of subsequent requests.
        
        Args:
            query_type (str): The type of query template to load (filename without .sql extension)
            
        Returns:
            str: The contents of the SQL template file
            
        Raises:
            FileNotFoundError: If the template file doesn't exist in the template directory
        """
        if query_type not in self.templates:
            template_path = os.path.join(self.template_dir, f"{query_type}.sql")
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"SQL template not found: {template_path}")
            
            with open(template_path, "r") as file:
                self.templates[query_type] = file.read()

        # Debug print statement to log template loading
        print(f"\n=== Loaded SQL Template for {query_type} ===\n{self.templates[query_type]}\n")

        return self.templates[query_type]
