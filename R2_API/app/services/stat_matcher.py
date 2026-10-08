import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
from enum import Enum
import json
import typer
import os
import re

# Base paths for storing ML model assets and indexes
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Navigate to project root
INDEX_BASEPATH = os.path.join(PROJECT_ROOT, 'app' ,'ml_assets')

# Map sport codes to their corresponding index files
INDEX_MAP = {
    sport_code : {
        fname.split(".")[0] : os.path.join(INDEX_BASEPATH, sport_code, fname) for fname in os.listdir(os.path.join(INDEX_BASEPATH, sport_code))
    } for sport_code in os.listdir(INDEX_BASEPATH)
}


class STModelChoice(Enum):
    """
    Enumeration for different SentenceTransformer model choices.
    Currently supports:
    - MINILM_L6_V2: A lightweight and efficient model for sentence embeddings
    """
    MINILM_L6_V2 = "all-MiniLM-L6-v2"


class StatIndex:
    """
    A class for indexing statistical mappings using SentenceTransformer embeddings.
    Provides functionality to create, save, and load statistical indexes for efficient similarity search.

    Attributes:
        stat_mapping_file (str): Path to the JSON file containing statistical mappings.
        encoding_model (STModelChoice): The SentenceTransformer model used for encoding.
        stat2ind (dict): Mapping of statistic names to their corresponding indices.
        ind2stat (list): List of statistic names indexed by their position.
        corpus_embeddings (list): Precomputed embeddings for statistics.
        model (SentenceTransformer): The SentenceTransformer model instance.
    """

    def __init__(self, stat_mapping_file, encoding_model: STModelChoice = STModelChoice.MINILM_L6_V2.value):
        """
        Initializes the StatIndex class by loading the statistical mapping and setting up the embedding model.

        Args:
            stat_mapping_file (str): Path to the statistical mapping JSON file.
            encoding_model (STModelChoice, optional): The encoding model to use. Defaults to STModelChoice.MINILM_L6_V2.
        """
        if stat_mapping_file:
            self.stat_mapping_file = stat_mapping_file
            self.stat_mapping = json.loads(open(stat_mapping_file).read())
        self.encoding_model = encoding_model
        self.stat2ind = {}
        self.ind2stat = []
        self.corpus_embeddings = []
        if not isinstance(self.encoding_model, str):
            self.encoding_model = self.encoding_model.value
        self.model = SentenceTransformer(self.encoding_model)

    # def create(self):
    #     """
    #     Creates the statistical index by generating embeddings for each statistic.
    #     Processes each statistic's name and description to create a corpus,
    #     then generates embeddings using the SentenceTransformer model.
    #     """
    #     corpus = [
    #         f"name: {stat['name']} | aliases : {','.join(stat.get('aliases', []))} | category: {stat.get('category', '')} | sub_category: {stat.get('sub_category', '')} | description: {stat['description']}"
    #         for stat in self.stat_mapping
    #     ]

    #     self.ind2stat = [stat['stat'] for stat in self.stat_mapping]
    #     self.stat2ind = {stat: i for i, stat in enumerate(self.ind2stat)}

    #     self.corpus_embeddings = self.model.encode(corpus)
    def create(self):
        """
        Creates the statistical index by generating embeddings for each statistic.
        Processes each statistic's name and description to create a corpus,
        then generates embeddings using the SentenceTransformer model.
        """
        corpus = [
            f"name: {stat['name']} | aliases : {','.join(stat.get('aliases', []))} | category: {stat.get('category', 'Unknown')} | sub_category: {stat.get('sub_category', '')} | description: {stat['description']}"
            for stat in self.stat_mapping
        ]

        self.ind2stat = [stat['stat'] for stat in self.stat_mapping]
        self.stat2ind = {stat: i for i, stat in enumerate(self.ind2stat)}

        self.corpus_embeddings = self.model.encode(corpus)



    def save(self, path: str):
        """
        Saves the statistical index to a file using pickle.
        Preserves all necessary components for later reconstruction of the index.

        Args:
            path (str): The file path where the index should be saved.
        """
        with open(path, 'wb') as f:
            all_objs = {
                'stat_mapping_file': self.stat_mapping_file,
                'stat_mapping': self.stat_mapping,
                'stat2ind': self.stat2ind,
                'ind2stat': self.ind2stat,
                'corpus_embeddings': self.corpus_embeddings,
                'encoding_model': str(self.encoding_model)
            }
            pickle.dump(all_objs, f)

    def load(self, path: str):
        """
        Loads the statistical index from a file using pickle.
        Reconstructs the index components and ensures model compatibility.

        Args:
            path (str): The file path from which to load the index.
        """
        with open(path, 'rb') as f:
            all_objs = pickle.load(f)
            self.stat_mapping_file = all_objs['stat_mapping_file']
            self.stat_mapping = all_objs['stat_mapping']
            self.stat2ind = all_objs['stat2ind']
            self.ind2stat = all_objs['ind2stat']
            self.corpus_embeddings = all_objs['corpus_embeddings']
            encoding_model = all_objs['encoding_model']
            if encoding_model != self.encoding_model:
                self.encoding_model = encoding_model
                print("Test" , self.encoding_model, isinstance(self.encoding_model, Enum))
                if not isinstance(self.encoding_model, str):
                    self.encoding_model = self.encoding_model.value
                self.model = SentenceTransformer(self.encoding_model)


class StatMatcher:
    """
    A class to match query statistics against the indexed statistical embeddings.
    Provides functionality for semantic similarity search across statistical descriptions.

    Attributes:
        index (StatIndex): An instance of StatIndex for performing queries.
        condition_splitter (re.Pattern): Regular expression to split query conditions.
    """

    def __init__(self, index: StatIndex):
        """
        Initializes the StatMatcher with a given StatIndex.

        Args:
            index (StatIndex): The statistical index to use for matching.
        """
        self.index = index
        self.condition_splitter = re.compile("AND|OR|WITHOUT", re.IGNORECASE)

    @staticmethod
    def from_sport_and_entity(sport_code: str, entity: str):
        """
        Creates a StatMatcher instance for a specific sport and entity combination.
        
        Args:
            sport_code (str): The code representing the sport (e.g., 'NBA', 'NFL')
            entity (str): The type of entity to match against (e.g., 'player', 'team')
            
        Returns:
            StatMatcher: A configured StatMatcher instance for the specified sport and entity
        """
        index_file = INDEX_MAP[sport_code][entity]
        print(f"[DEBUG] Attempting to load index file for {sport_code}/{entity}: {index_file}")

        if not index_file or not os.path.exists(index_file):
            print(f"[ERROR] Index file not found for {sport_code}/{entity}")
            return None
        index = StatIndex(None)
        index.load(index_file)
        return StatMatcher(index)

    @staticmethod
    def get_all_stat_matchers():
        """
        Creates a dictionary of StatMatcher instances for all available sport and entity combinations.
        
        Returns:
            dict: A nested dictionary mapping sport codes and entities to their respective StatMatcher instances
        """
        stat_matchers = {}
        for sport_code, entities in INDEX_MAP.items():
            stat_matchers[sport_code] = {}
            for entity in entities:
                stat_matchers[sport_code][entity] = StatMatcher.from_sport_and_entity(sport_code, entity)
        return stat_matchers

    def match(self, query: str, top_k: int = 10):
        """
        Matches a query against the indexed statistics and returns the top-k matches.
        Splits the query into components, computes embeddings, and finds the most similar statistics.

        Args:
            query (str): The input query string to match against the statistical corpus
            top_k (int, optional): The number of top matches to return. Defaults to 10.

        Returns:
            list: A list of dictionaries containing the top-k matching statistics with their metadata
        """
        query_components = self.condition_splitter.split(query)
        query_embeddings = self.index.model.encode(query_components)
        scores = self.index.model.similarity(self.index.corpus_embeddings, query_embeddings)

                # Additional Debugging
        print(f"[DEBUG] Query Embeddings: {query_embeddings.shape}")
        print(f"[DEBUG] Corpus Embeddings: {len(self.index.corpus_embeddings)} entries")
   
        all_top_k_choices = []
        for i in range(scores.shape[1]):
            score_col = scores[:, i]
            top_k_choices = np.argpartition(score_col, -top_k)[-top_k:]
            all_top_k_choices += top_k_choices
        all_top_k_choices = list(set(all_top_k_choices))
        all_top_k_choices = [self.index.stat_mapping[i] for i in all_top_k_choices]
        return all_top_k_choices


def test_stat_matching_with_sample(stat_mapping_file: str, test_file: str, output_file: str, top_k: int = 10):
    """
    Tests the statistical matching process with sample queries and evaluates accuracy.
    Processes a set of test queries, compares results against known correct matches,
    and generates a detailed report of matching performance.

    Args:
        stat_mapping_file (str): Path to the statistical mapping JSON file
        test_file (str): Path to the test queries JSON file
        output_file (str): Path to save the test results
        top_k (int, optional): The number of top matches to consider. Defaults to 10.
    """
    just_stats = re.compile("s[a-zA-Z]+[0-9]*[a-zA-Z]*")
    stat_index = StatIndex(stat_mapping_file)

    s = time.time()
    stat_index.create()
    e = time.time()

    print(f"Stat Mapping Index Creation took {e - s:.2f} seconds")

    test_queries = json.loads(open(test_file).read())

    test_queries = [(x["query"], just_stats.findall(x["aql"]["conditions"])) for x in test_queries]
    stat_mat = StatMatcher(stat_index)
    avg_stat_matching_time = 0

    in_top_5 = 0
    total_stats = 0
    new_collection = []

    for query in test_queries:
        s = time.time()
        top_k_matches = stat_mat.match(query[0], top_k=top_k)
        e = time.time()
        avg_stat_matching_time += (e - s)

        top_k_stats = [x["stat"] for x in top_k_matches]
        matched_stats = 0
        for stat in query[1]:
            if stat in top_k_stats:
                matched_stats += 1
            total_stats += 1

        in_top_5 += matched_stats
        new_collection.append({
            "query": query[0],
            "matched_stats": top_k_stats,
            "real_stats": query[1],
            "unmatched_stats": len(query[1]) - matched_stats,
        })

    print(
        f"Total stats: {total_stats}, Matched : {in_top_5}. Accuracy : {in_top_5 / total_stats}, Avg Matching Time : {avg_stat_matching_time / len(test_queries)}")
    with open(output_file, "w") as f:
        f.write(json.dumps(new_collection, indent=4))


if __name__ == '__main__':
    import time
    import re

    app = typer.Typer()

    @app.command("create")
    def create_index(stat_mapping_file: str, save_path: str):
        """
        CLI command to create and save a new statistical index.

        Args:
            stat_mapping_file (str): Path to the statistical mapping JSON file
            save_path (str): Path where the created index should be saved
        """
        stat_index = StatIndex(stat_mapping_file)

        s = time.time()
        stat_index.create()
        e = time.time()

        print(f"Stat Mapping Index Creation took {e - s:.2f} seconds")
        stat_index.save(save_path)

    @app.command("test")
    def test(stat_mapping_file: str, test_file: str, output_file: str, top_k: int = 10):
        """
        CLI command to run statistical matching tests.

        Args:
            stat_mapping_file (str): Path to the statistical mapping JSON file
            test_file (str): Path to the test queries JSON file
            output_file (str): Path to save the test results
            top_k (int, optional): Number of top matches to consider. Defaults to 10.
        """
        test_stat_matching_with_sample(stat_mapping_file, test_file, output_file, top_k)

    @app.command("query")
    def query(index_file: str, query: str, top_k: int = 10):
        """
        CLI command to perform a single query against a statistical index.

        Args:
            index_file (str): Path to the saved statistical index
            query (str): The query string to match
            top_k (int, optional): Number of top matches to return. Defaults to 10.
        """
        stat_index = StatIndex(None)
        stat_index.load(index_file)
        stat_mat = StatMatcher(stat_index)
        s = time.time()
        results = stat_mat.match(query, top_k=top_k)
        e = time.time()
        print(json.dumps(results, indent=4))
        print(f"Query took {e - s:.2f} seconds")

    app()
