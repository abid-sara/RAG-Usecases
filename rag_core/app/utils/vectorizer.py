import re
import nltk
import numpy as np
import torch
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi
from transformers import AutoTokenizer, AutoModel
from app.utils.transformers_patch import patch_transformers
import logging
import os
from nltk.corpus import stopwords
from huggingface_hub import login

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Apply the patch for transformers
patch_transformers()

class HybridVectorizer:
    def __init__(self, english_embedding_model="sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the hybrid vectorizer with TF-IDF, BM25, and word embeddings for English data.

        Args:
            english_embedding_model (str): HuggingFace model path for English embeddings
        """
        
        logger = logging.getLogger(__name__)

        # Authenticate with Hugging Face if token is available
        try:
            hf_token = os.environ.get('HUGGINGFACE_TOKEN')
            if hf_token:
                login(token=hf_token)
                logger.info("Logged in to Hugging Face with token from environment")
        except Exception as e:
            logger.warning(f"Could not authenticate with Hugging Face: {e}")

        # Download NLTK stopwords and punkt tokenizer
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except Exception as e:
            logger.warning(f"Could not download NLTK data: {e}")

        # Use minimal stopwords
        self.minimal_stopwords = {'a', 'an', 'the', 'and', 'or', 'but'}

        # Initialize vectorizers with more lenient settings
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),  # Allow 1-3 word phrases
            min_df=1,  # Accept terms that appear at least once
            max_df=0.95,  # More lenient with common terms
            stop_words=None,  # Don't remove stopwords at vectorizer level
            sublinear_tf=True
        )

        self.bm25 = None

        # Load English embedding model
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        try:
            logger.info(f"Loading English embedding model: {english_embedding_model}")
            self.tokenizer = AutoTokenizer.from_pretrained(english_embedding_model)

            with torch.no_grad():
                self.model = AutoModel.from_pretrained(english_embedding_model).to(self.device)
                self.model.eval()

            logger.info(f"English embedding model loaded on {self.device}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            self.tokenizer = None
            self.model = None

        # Storage for documents and vectors
        self.chunks = []
        self.preprocessed_chunks = []
        self.tokenized_chunks = []
        self.tfidf_vectors = None
        self.embedding_vectors = None

        self.is_fitted = False

        self.weights = {
            'tfidf': 0.3,
            'bm25': 0.3,
            'embeddings': 0.4
        }

    def normalize_english_text(self, text):
        """Clean English text while preserving meaningful content."""
        if not isinstance(text, str):
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but preserve dots, dashes, and parentheses
        text = re.sub(r'[^a-zA-Z0-9\s\.\-\(\)]', ' ', text)
        
        return text.strip()

    def preprocess_english_text(self, text):
        """Preprocess English text for better search results."""
        # Normalize text
        text = self.normalize_english_text(text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove only minimal stopwords
        tokens = [token for token in tokens if token not in self.minimal_stopwords]
        
        # Join tokens back preserving more of the original text
        return tokens, ' '.join(tokens)

    def prepare_chunk_text(self, chunk):
        """Combine text with section title for better context."""
        try:
            section = chunk.get('section_title', '').strip()
            text = chunk.get('text', '').strip()
            document = chunk.get('document', '').strip()
            
            # Combine document title, section, and text for better context
            if section and document:
                return f"{document} - {section}: {text}"
            elif document:
                return f"{document}: {text}"
            return text
        except Exception as e:
            logger.error(f"Error preparing chunk text: {e}")
            return chunk.get('text', '')

    def get_embeddings(self, texts):
        """Generate embeddings for a list of texts using the embedding model"""
        if self.model is None or self.tokenizer is None:
            return None
        
        embeddings = []
        batch_size = 8  # Process in batches to avoid memory issues
        
        self.model.eval()  # Set model to evaluation mode
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                inputs = self.tokenizer(batch_texts, padding=True, truncation=True, 
                                       max_length=512, return_tensors="pt").to(self.device)
                
                outputs = self.model(**inputs)
                
                # Use CLS token embedding as the sentence embedding
                batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                embeddings.extend(batch_embeddings)
        
        return np.array(embeddings)
    
    def fit(self, chunks):
        """Fit the hybrid vectorizer on document chunks"""
        logger.info(f"Starting to fit vectorizer with {len(chunks)} chunks")
        
        # Handle case where chunks is None or empty
        if not chunks:
            logger.warning("No document chunks provided to fit. Vectorizer remains unfitted.")
            self.is_fitted = False
            return False
            
        self.chunks = chunks
        
        # Preprocess chunks
        tokenized_chunks = []
        preprocessed_chunks = []
        
        for chunk in chunks:
            # Prepare text with context
            text = self.prepare_chunk_text(chunk)
            tokens, preprocessed = self.preprocess_english_text(text)
            
            # Debug logging
            logger.debug(f"Original chunk: {text[:200]}")
            logger.debug(f"Preprocessed chunk: {preprocessed[:200]}")
            logger.debug(f"Number of tokens: {len(tokens)}")
            
            tokenized_chunks.append(tokens)
            preprocessed_chunks.append(preprocessed)
        
        self.tokenized_chunks = tokenized_chunks
        self.preprocessed_chunks = preprocessed_chunks
        
        try:
            # Fit TF-IDF
            logger.info("Fitting TF-IDF vectorizer...")
            self.tfidf_vectors = self.tfidf_vectorizer.fit_transform(preprocessed_chunks)
            logger.info(f"TF-IDF vectorizer fitted successfully with {self.tfidf_vectors.shape[1]} features")
            
            # Initialize BM25
            logger.info("Initializing BM25...")
            self.bm25 = BM25Okapi(tokenized_chunks)
            logger.info("BM25 model initialized")
            
            # Generate embeddings
            if self.model is not None:
                logger.info("Generating embeddings for document chunks...")
                self.embedding_vectors = self.get_embeddings(preprocessed_chunks)
                logger.info(f"Generated embeddings with shape: {self.embedding_vectors.shape}")
            else:
                logger.warning("Embedding model not available, will rely on TF-IDF and BM25 only")
            
            # Set fitted flag to True
            self.is_fitted = True
            logger.info("Vectorizer fitting completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error during vectorizer fitting: {e}")
            self.is_fitted = False
            return False
    
    def set_weights(self, tfidf_weight=0.3, bm25_weight=0.3, embedding_weight=0.4):
        """Set weights for hybrid search components"""
        self.weights = {
            'tfidf': tfidf_weight,
            'bm25': bm25_weight,
            'embeddings': embedding_weight
        }
        
        # Normalize weights to sum to 1
        weight_sum = sum(self.weights.values())
        for key in self.weights:
            self.weights[key] /= weight_sum
        
        logger.info(f"Search weights set to: {self.weights}")
    
    def search(self, query, top_n=10, method='hybrid'):
        """
        Search for relevant documents using specified search method
        
        Args:
            query (str): The search query
            top_n (int): Number of results to return
            method (str): Search method to use ('hybrid', 'tfidf', 'bm25', 'embeddings')
        """
        valid_methods = ['hybrid', 'tfidf', 'bm25', 'embeddings']
        if method not in valid_methods:
            logger.warning(f"Invalid search method: {method}. Using 'hybrid' instead.")
            method = 'hybrid'
            
        # Check if vectorizer has been fitted
        if not self.is_fitted:
            logger.warning("Vectorizer hasn't been fitted with documents yet. Returning empty results.")
            return []
        
        # Check if we have documents to search
        if not self.chunks:
            logger.warning("No documents to search. Returning empty results.")
            return []
        
        # Preprocess query
        query_tokens, preprocessed_query = self.preprocess_english_text(query)
        logger.debug(f"Preprocessed query: {preprocessed_query}")
        
        # Get scores based on method
        if method == 'tfidf':
            return self._tfidf_search(preprocessed_query, top_n)
        elif method == 'bm25':
            return self._bm25_search(query_tokens, top_n)
        elif method == 'embeddings':
            return self._embedding_search(preprocessed_query, top_n)
        else:  # hybrid (default)
            return self._hybrid_search(query_tokens, preprocessed_query, top_n)
    
    def _tfidf_search(self, preprocessed_query, top_n):
        """Search using TF-IDF only"""
        # Safety check
        if self.tfidf_vectors is None or not self.is_fitted:
            logger.warning("TF-IDF vectors not available. Returning empty results.")
            return []
            
        # TF-IDF scoring
        try:
            tfidf_query_vector = self.tfidf_vectorizer.transform([preprocessed_query])
            tfidf_scores = np.asarray(tfidf_query_vector.dot(self.tfidf_vectors.T).toarray())[0]
            
            # Combine chunks with scores and sort
            chunk_score_pairs = list(zip(self.chunks, tfidf_scores.tolist()))
            ranked_chunks = sorted(chunk_score_pairs, key=lambda x: x[1], reverse=True)
            
            # Return top N results
            return ranked_chunks[:top_n]
        except Exception as e:
            logger.error(f"Error in TF-IDF search: {e}")
            return []
    
    def _bm25_search(self, query_tokens, top_n):
        """Search using BM25 only"""
        # Safety check
        if self.bm25 is None or not self.is_fitted:
            logger.warning("BM25 model not available. Returning empty results.")
            return []
            
        try:
            # BM25 scoring
            bm25_scores = np.array(self.bm25.get_scores(query_tokens))
            
            # Combine chunks with scores and sort
            chunk_score_pairs = list(zip(self.chunks, bm25_scores.tolist()))
            ranked_chunks = sorted(chunk_score_pairs, key=lambda x: x[1], reverse=True)
            
            # Return top N results
            return ranked_chunks[:top_n]
        except Exception as e:
            logger.error(f"Error in BM25 search: {e}")
            return []
    
    def _embedding_search(self, preprocessed_query, top_n):
        """Search using embeddings only"""
        if self.model is None or self.embedding_vectors is None or not self.is_fitted:
            logger.warning("Embedding model or vectors not available. Falling back to TF-IDF.")
            return self._tfidf_search(preprocessed_query, top_n)
        
        try:
            # Generate query embedding
            query_embedding = self.get_embeddings([preprocessed_query])[0]
            
            # Calculate cosine similarity
            similarity = torch.nn.functional.cosine_similarity(
                torch.tensor(query_embedding).unsqueeze(0),
                torch.tensor(self.embedding_vectors),
                dim=1
            ).numpy()
            
            # Combine chunks with scores and sort
            chunk_score_pairs = list(zip(self.chunks, similarity.tolist()))
            ranked_chunks = sorted(chunk_score_pairs, key=lambda x: x[1], reverse=True)
            
            # Return top N results
            return ranked_chunks[:top_n]
        except Exception as e:
            logger.error(f"Error in embedding search: {e}")
            return self._tfidf_search(preprocessed_query, top_n)  # Fallback
    
    def _hybrid_search(self, query_tokens, preprocessed_query, top_n):
        """
        Search for relevant documents using hybrid approach combining
        TF-IDF, BM25, and embeddings
        """
        # Safety check
        if not self.is_fitted:
            logger.warning("Vectorizer not fitted. Returning empty results.")
            return []
            
        try:
            # --- TF-IDF scoring ---
            tfidf_scores = np.zeros(len(self.chunks))
            if self.tfidf_vectors is not None:
                tfidf_query_vector = self.tfidf_vectorizer.transform([preprocessed_query])
                tfidf_scores = np.asarray(tfidf_query_vector.dot(self.tfidf_vectors.T).toarray())[0]
                
                # Normalize TF-IDF scores
                tfidf_max = np.max(tfidf_scores) if np.max(tfidf_scores) > 0 else 1
                tfidf_scores = tfidf_scores / tfidf_max
            
            # --- BM25 scoring ---
            bm25_scores = np.zeros(len(self.chunks))
            if self.bm25 is not None:
                bm25_scores = np.array(self.bm25.get_scores(query_tokens))
                
                # Normalize BM25 scores
                bm25_max = np.max(bm25_scores) if np.max(bm25_scores) > 0 else 1
                bm25_scores = bm25_scores / bm25_max
            
            # --- Embedding similarity scoring ---
            embedding_scores = np.zeros(len(self.chunks))
            if self.model is not None and self.embedding_vectors is not None:
                query_embedding = self.get_embeddings([preprocessed_query])[0]
                
                # Calculate cosine similarity between query and document embeddings
                similarity = torch.nn.functional.cosine_similarity(
                    torch.tensor(query_embedding).unsqueeze(0),
                    torch.tensor(self.embedding_vectors),
                    dim=1
                ).numpy()
                
                embedding_scores = (similarity + 1) / 2  # Normalize from [-1,1] to [0,1]
            
            # --- Exact match and term match bonuses ---
            exact_match_scores = np.zeros(len(self.chunks))
            for i, chunk in enumerate(self.preprocessed_chunks):
                # Bonus for exact phrase match
                if preprocessed_query in chunk:
                    exact_match_scores[i] += 0.3
                
                # Count term matches and add proportional bonus
                term_matches = sum(1 for term in query_tokens if term in self.tokenized_chunks[i])
                term_match_ratio = term_matches / len(query_tokens) if query_tokens else 0
                exact_match_scores[i] += term_match_ratio * 0.2
            
            # --- Combine scores with configured weights ---
            combined_scores = (
                self.weights['tfidf'] * tfidf_scores +
                self.weights['bm25'] * bm25_scores +
                self.weights['embeddings'] * embedding_scores +
                0.2 * exact_match_scores  # 20% weight for exact matches
            )
            
            # Combine chunks with scores and sort
            chunk_score_pairs = list(zip(self.chunks, combined_scores.tolist()))
            ranked_chunks = sorted(chunk_score_pairs, key=lambda x: x[1], reverse=True)
            
            # Return top N results
            return ranked_chunks[:top_n]
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}. Returning empty results.")
            return []