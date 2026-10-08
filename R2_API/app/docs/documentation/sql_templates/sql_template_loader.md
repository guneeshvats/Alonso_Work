# Documentation for `sql_template_loader.py`

# SQLTemplateLoader: Technical Documentation

## Overview

The `SQLTemplateLoader` class is designed to facilitate the loading and caching of SQL template files. These templates are stored as text files in a specified directory and are intended to be used in applications where SQL query templates are needed frequently, such as in database-driven applications. By caching these templates in memory, the class optimizes performance, reducing the need to repeatedly access the filesystem. 

## Class: SQLTemplateLoader

### Purpose

The `SQLTemplateLoader` class handles the following tasks:
- Initialization and loading of all SQL templates from a specified directory into memory.
- On-demand retrieval of SQL templates, which includes lazy loading of templates that were not pre-loaded during initialization.
- Caching of loaded templates to minimize file I/O operations and improve performance.

### Attributes

- `template_dir` (str): Represents the directory path containing the SQL template files. By default, it is set to `'app/sql_templates'`.
- `templates` (dict): A dictionary used to cache the loaded SQL templates. The keys are the query types (derived from the filenames of the templates), and the values are the SQL content as strings.

### Methods

#### `__init__(self, template_dir="app/sql_templates")`

**Purpose**: Initializes an instance of the `SQLTemplateLoader` class, setting up the directory from which SQL templates will be loaded.

**Arguments**:
- `template_dir` (str): The path to the directory containing the SQL template files. Defaults to `'app/sql_templates'`.

**Behavior**: 
- On instantiation, the constructor reads all files with a `.sql` extension from the specified directory and loads their content into the `templates` dictionary. The key for each entry in the dictionary is derived from the filename by removing the `.sql` extension.

**Implementation Details**:
- Uses `os.listdir()` to list files in the specified directory.
- Filters files to include only those ending with `.sql`.
- Opens each SQL file, reads its content, and stores it in the `templates` dictionary using the filename (minus the `.sql` extension) as the key.

#### `load_template(self, query_type)`

**Purpose**: Retrieves an SQL template corresponding to a given query type.

**Arguments**:
- `query_type` (str): The type of query template to be loaded. This corresponds to the filename without the `.sql` extension.

**Returns**: 
- A string containing the content of the SQL template file.

**Behavior**:
- Checks if the requested template is available in the `templates` cache. 
- If the template is not cached, attempts to load it from the filesystem, caches it, and then returns the content.
- Raises a `FileNotFoundError` if the template does not exist in the specified directory.

**Implementation Details**:
- Constructs the full path to the template file using `os.path.join()`.
- Uses `os.path.exists()` to verify the existence of the file before attempting to open it.
- Includes a debug print statement to log the loading of SQL templates for tracking purposes.

## Dependencies

- **os**: The script uses the `os` module to interact with the operating system, particularly for directory listing (`os.listdir`), path manipulation (`os.path.join`), and file existence checking (`os.path.exists`).
- **app.constants.Qualifiers**: Although imported, this constant or module is not utilized within the current implementation of the class. It may be reserved for future use or required elsewhere in the application.
