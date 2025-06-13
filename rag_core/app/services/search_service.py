import json
import logging
import os
import numpy as np
import faiss
import pickle
from app.utils.vectorizer import HybridVectorizer
from rank_bm25 import BM25Okapi  # Import added here
from config.settings import TOP_N_RESULTS, DEFAULT_SEARCH_METHOD

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, DATA_PATH, VECTOR_DB_PATH ,embedding_model="asafaya/bert-base-arabic", 
                 tfidf_weight=0.3, bm25_weight=0.3, embedding_weight=0.4,
                 search_method=None
                 ):
        """
        Initialize the enhanced search service with hybrid vectorization
        
        Args:
            embedding_model (str): HuggingFace model path for Arabic embeddings
            tfidf_weight (float): Weight for TF-IDF scores in hybrid search
            bm25_weight (float): Weight for BM25 scores in hybrid search
            embedding_weight (float): Weight for embedding similarity in hybrid search
            search_method (str): Method to use for search ('hybrid', 'tfidf', 'bm25', 'embeddings')
                                 If None, uses the DEFAULT_SEARCH_METHOD from settings
        """
        # Create directory for data file if it doesn't exist
        data_dir = os.path.dirname(DATA_PATH)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        # Create directory for vector DB if it doesn't exist
        vector_db_dir = os.path.dirname(VECTOR_DB_PATH)
        if not os.path.exists(vector_db_dir):
            os.makedirs(vector_db_dir)
            
        # Set search method (use default from settings if not specified)
        self.search_method = search_method or DEFAULT_SEARCH_METHOD
        logger.info(f"Initializing SearchService with search method: {self.search_method}")
            
        self.vectorizer = HybridVectorizer(english_embedding_model=embedding_model)
        self.vectorizer.set_weights(
            tfidf_weight=tfidf_weight,
            bm25_weight=bm25_weight,
            embedding_weight=embedding_weight
        )
        self.chunks = []
        self.vector_index = None
        self.metadata = {}
        self.is_fitted = False
        
        # Load data during initialization
        self.load_data()
        
    def load_data(self):
        """Load document chunks from JSON file and vector database"""
        try:
            if not os.path.exists(self.DATA_PATH):
                logger.warning(f"Data file {self.DATA_PATH} does not exist.")
                self.chunks = []
                return False
                
            # Load document chunks
            with open(self.DATA_PATH, 'r', encoding='utf-8') as file:
                self.chunks = json.load(file)
                
            if not self.chunks:
                logger.warning("No document chunks found in data file")
                return False
                
            logger.info(f"Loaded {len(self.chunks)} document chunks from {self.DATA_PATH}")
            
            # Check if vector database exists
            vector_db_exists = os.path.exists(self.VECTOR_DB_PATH)
            metadata_exists = os.path.exists(f"{self.VECTOR_DB_PATH}.meta")
            
            if vector_db_exists and metadata_exists:
                # Load existing vector database
                success = self._load_vector_db()
                if not success:
                    # If loading fails, build a new one
                    success = self._build_vector_db()
            else:
                # Build new vector database
                success = self._build_vector_db()
                
            self.is_fitted = success
            logger.info(f"After loading, SearchService has {len(self.chunks)} chunks")
            logger.info(f"After loading, Vectorizer has {len(self.vectorizer.chunks)} chunks")
            return success
        
        except Exception as e:
            logger.error(f"Error loading document chunks: {e}")
            self.chunks = []
            self.is_fitted = False
            return False
    
    def _load_vector_db(self):
        """Load existing vector database and metadata"""
        try:
            # Load FAISS index
            self.vector_index = faiss.read_index(self.VECTOR_DB_PATH)
            
            # Load metadata
            with open(f"{self.VECTOR_DB_PATH}.meta", 'rb') as f:
                self.metadata = pickle.load(f)
            
            # Restore vectorizer state
            self.vectorizer.tfidf_vectorizer = self.metadata.get('tfidf_vectorizer')
            self.vectorizer.tfidf_vectors = self.metadata.get('tfidf_vectors')
            self.vectorizer.bm25 = self.metadata.get('bm25')
            self.vectorizer.tokenized_chunks = self.metadata.get('tokenized_chunks', [])
            self.vectorizer.preprocessed_chunks = self.metadata.get('preprocessed_chunks', [])
            self.vectorizer.embedding_vectors = self.metadata.get('embedding_vectors')

            # Set the chunks in the vectorizer
            self.vectorizer.chunks = self.chunks

            # Set the fitted flag on the vectorizer
            self.vectorizer.is_fitted = True
            
            # Verify integrity - check if vector count matches chunk count
            if self.vector_index.ntotal != len(self.chunks):
                logger.warning("Vector index size doesn't match chunk count. Rebuilding index.")
                return self._build_vector_db()
                
            logger.info(f"Successfully loaded vector database with {self.vector_index.ntotal} vectors")
            return True
        except Exception as e:
            logger.error(f"Error loading vector database: {e}")
            return False
    
    def _build_vector_db(self):
        """Build vector database from scratch"""
        logger.info("Building vector database from chunks...")
        
        if not self.chunks:
            logger.warning("No chunks available to build vector database")
            return False
            
        # Fit the vectorizer with chunks
        try:
            success = self.vectorizer.fit(self.chunks)
            if not success:
                logger.error("Failed to fit vectorizer with chunks")
                return False
            
            # Make sure is_fitted is synchronized (redundant but for safety)
            if not self.vectorizer.is_fitted:
                logger.error("Vectorizer not fitted despite successful fit operation")
                return False
                
            # Verify embedding vectors were created
            if self.vectorizer.embedding_vectors is None:
                logger.error("Embedding vectors not generated during vectorizer fitting")
                return False
                
            # Create FAISS index
            embedding_dim = self.vectorizer.embedding_vectors.shape[1]
            self.vector_index = faiss.IndexFlatL2(embedding_dim)
            
            # Add vectors to index
            vectors = np.array(self.vectorizer.embedding_vectors).astype('float32')
            self.vector_index.add(vectors)
            
            # Save vector database and metadata
            self._save_vector_db()
            
            logger.info(f"Built vector database with {len(self.chunks)} chunks")
            return True
        except Exception as e:
            logger.error(f"Error building vector database: {e}")
            return False
    
    def _save_vector_db(self):
        """Save vector database and metadata to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.vector_index, self.VECTOR_DB_PATH)
            
            # Save metadata for hybrid search components
            self.metadata = {
                'tfidf_vectorizer': self.vectorizer.tfidf_vectorizer,
                'tfidf_vectors': self.vectorizer.tfidf_vectors,
                'bm25': self.vectorizer.bm25,
                'tokenized_chunks': self.vectorizer.tokenized_chunks,
                'preprocessed_chunks': self.vectorizer.preprocessed_chunks,
                'embedding_vectors': self.vectorizer.embedding_vectors,
                'last_updated': np.datetime64('now')
            }
            
            with open(f"{self.VECTOR_DB_PATH}.meta", 'wb') as f:
                pickle.dump(self.metadata, f)
                
            logger.info(f"Saved vector database to {self.VECTOR_DB_PATH}")
            return True
        except Exception as e:
            logger.error(f"Error saving vector database: {e}")
            return False
    
    def add_documents(self, new_chunks):
        """
        Add new documents to the system and update vector database
        
        Args:
            new_chunks (list): List of new document chunks to add
        """
        if not new_chunks:
            return False
            
        try:
            # If not fitted yet, fit with all chunks
            if not self.is_fitted:
                self.chunks.extend(new_chunks)
                return self._build_vector_db()
                
            # Process new chunks
            start_idx = len(self.chunks)
            self.chunks.extend(new_chunks)
            
            # Preprocess new chunks
            tokenized_new = []
            preprocessed_new = []
            
            for chunk in new_chunks:
                tokens, preprocessed = self.vectorizer.preprocess_arabic_text(chunk)
                tokenized_new.append(tokens)
                preprocessed_new.append(preprocessed)
            
            # Update vectorizer data structures
            self.vectorizer.tokenized_chunks.extend(tokenized_new)
            self.vectorizer.preprocessed_chunks.extend(preprocessed_new)
            
            # Generate embeddings for new chunks only
            new_embeddings = self.vectorizer.get_embeddings(preprocessed_new)
            
            # Add to vector index
            if new_embeddings is not None:
                self.vector_index.add(np.array(new_embeddings).astype('float32'))
                
                # Update embedding vectors in vectorizer
                if self.vectorizer.embedding_vectors is not None:
                    self.vectorizer.embedding_vectors = np.vstack([
                        self.vectorizer.embedding_vectors, 
                        new_embeddings
                    ])
            
            # Update TF-IDF and BM25 (unfortunately requires recomputing)
            # Re-fit TF-IDF
            self.vectorizer.tfidf_vectors = self.vectorizer.tfidf_vectorizer.fit_transform(
                self.vectorizer.preprocessed_chunks
            )
            
            # Re-initialize BM25
            self.vectorizer.bm25 = BM25Okapi(self.vectorizer.tokenized_chunks)
            
            # Save updated database
            with open(self.DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.chunks, f, ensure_ascii=False)
                
            # Save updated vector database
            self._save_vector_db()
            
            logger.info(f"Added {len(new_chunks)} new document chunks to database")
            return True
        except Exception as e:
            logger.error(f"Error adding new documents: {e}")
            return False
    
    def search(self, query, top_n=10, search_method='hybrid'):
        """
        Search for relevant documents using specified search method
        
        Args:
            query (str): The search query
            top_n (int): Number of results to return
            method (str): Search method to use ('hybrid', 'tfidf', 'bm25', 'embeddings')
        """
        valid_methods = ['hybrid', 'tfidf', 'bm25', 'embeddings']
        if search_method not in valid_methods:
            logger.warning(f"Invalid search method: {search_method}. Using 'hybrid' instead.")
            search_method = 'hybrid'
            
        # Check if vectorizer has been fitted
        if not self.is_fitted:
            logger.warning("Vectorizer hasn't been fitted with documents yet. Returning empty results.")
            return []  # Return empty list instead of raising exception
            
        # Log the size of chunks in the vectorizer
        logger.info(f"Vectorizer has {len(self.chunks)} chunks for search")
            
        # Check if we have documents to search
        if not self.chunks:
            logger.warning("No documents to search. Returning empty results.")
            return []
            
        # Check if all required components are available
        if self.vectorizer.tfidf_vectors is None:
            logger.error("TF-IDF vectors not available. Vectorizer may not be properly fitted.")
            return []
            
        if self.vectorizer.bm25 is None:
            logger.error("BM25 model not available. Vectorizer may not be properly fitted.")
            return []
            
        # Use method parameter if provided, otherwise use instance default
        method = search_method or self.search_method
            
        try:
            logger.info(f"Searching for '{query}' with method={method}, top_n={top_n}")
            
            if method == 'embeddings':
                # Use direct vector search for pure embedding search
                results = self._vector_search(query, top_n)
            else:
                # Use hybrid search from vectorizer which now uses persisted embeddings
                results = self.vectorizer.search(query, top_n, method=method)
                
            logger.info(f"Found {len(results)} relevant results using {method} search")
            return results
        except Exception as e:
            logger.error(f"Error during search: {e}")
            
            # If first search attempt failed, try to rebuild vector database and retry
            if "Vectorizer hasn't been fitted" in str(e):
                logger.info("Attempting to rebuild vector database and retry search...")
                if self._build_vector_db():
                    try:
                        if method == 'embeddings':
                            results = self._vector_search(query, top_n)
                        else:
                            results = self.vectorizer.search(query, top_n, method=method)
                        logger.info(f"Retry successful. Found {len(results)} results.")
                        return results
                    except Exception as retry_e:
                        logger.error(f"Retry search also failed: {retry_e}")
            
            return []
    
    def _vector_search(self, query, top_n):
        """Perform vector similarity search using FAISS"""
        if self.vector_index is None:
            raise ValueError("Vector index not initialized")
            
        if self.vector_index.ntotal == 0:
            logger.warning("Vector index is empty")
            return []
            
        # Preprocess query
        _, preprocessed_query = self.vectorizer.preprocess_arabic_text(query)
        
        # Get query embedding
        query_embedding = self.vectorizer.get_embeddings([preprocessed_query])
        if query_embedding is None or len(query_embedding) == 0:
            logger.error("Failed to generate query embedding")
            return []
            
        query_vector = query_embedding[0].reshape(1, -1).astype('float32')
        
        # Search in vector index
        distances, indices = self.vector_index.search(query_vector, k=min(top_n, self.vector_index.ntotal))
        
        # Format results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.chunks):  # Valid index
                # Convert distance to similarity score (inverse relationship)
                similarity = 1.0 / (1.0 + distances[0][i])
                results.append((self.chunks[idx], float(similarity)))
        
        return results
    
    def format_search_results(self, results):
        """Format search results for QA system"""
        formatted_chunks = []
        for i, (chunk, score) in enumerate(results, 1):
            formatted_chunks.append(f"{i}. {chunk}")
        
        return formatted_chunks
        
    def set_search_method(self, method):
        """
        Set the default search method for this instance
        
        Args:
            method (str): One of 'hybrid', 'tfidf', 'bm25', 'embeddings'
        """
        valid_methods = ['hybrid', 'tfidf', 'bm25', 'embeddings']
        if method not in valid_methods:
            logger.warning(f"Invalid search method: {method}. Using 'hybrid' instead.")
            method = 'hybrid'
            
        self.search_method = method
        logger.info(f"Search method set to: {method}")
        return True