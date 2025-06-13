from collections import deque
import datetime
import logging
from flask import Blueprint, request, jsonify, session
from flask_cors import cross_origin
from app.services.search_service import SearchService
from app.services.qa_service import QAService
from app.utils.conversation_manager import ConversationManager
from werkzeug.exceptions import BadRequestKeyError, RequestEntityTooLarge


from config.settings import (
    EMBEDDING_MODEL, TFIDF_WEIGHT, BM25_WEIGHT, EMBEDDING_WEIGHT,
    DEFAULT_SEARCH_METHOD, CONVERSATION_EXPIRY_TIME, MAX_CONVERSATION_LENGTH, TOP_N_RESULTS, SATIM_DATA_PATH,
    SATIM_VECTOR_DB_PATH, INTL_DATA_PATH, INTL_VECTOR_DB_PATH
)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize services
satim_search = SearchService(
    DATA_PATH=SATIM_DATA_PATH,
    VECTOR_DB_PATH=SATIM_VECTOR_DB_PATH,
    embedding_model=EMBEDDING_MODEL,
    tfidf_weight=TFIDF_WEIGHT,
    bm25_weight=BM25_WEIGHT,
    embedding_weight=EMBEDDING_WEIGHT,
    search_method=DEFAULT_SEARCH_METHOD
)

intl_search = SearchService(
    DATA_PATH=INTL_DATA_PATH,
    VECTOR_DB_PATH=INTL_VECTOR_DB_PATH,
    embedding_model=EMBEDDING_MODEL,
    tfidf_weight=TFIDF_WEIGHT,
    bm25_weight=BM25_WEIGHT,
    embedding_weight=EMBEDDING_WEIGHT,
    search_method=DEFAULT_SEARCH_METHOD
)
qa_service = QAService(satim_search, intl_search)

# Initialize conversation manager
conversation_manager = ConversationManager(
    max_conversation_length=MAX_CONVERSATION_LENGTH,
    expiry_time=CONVERSATION_EXPIRY_TIME
)

# Create Blueprint
api = Blueprint('api', __name__)

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for both databases"""
    return jsonify({
        'status': 'healthy',
        'satim': {
            'documents': satim_search.get_document_count(),
            'index_status': satim_search.get_index_stats()
        },
        'international': {
            'documents': intl_search.get_document_count(),
            'index_status': intl_search.get_index_stats()
        },
        'qa_service': 'operational'
    }), 200


@api.route('/search', methods=['POST'])
def search():
    """
    Search endpoint that searches both SATIM and International databases
    
    Expected JSON payload:
    {
        "query": "search query",
        "top_n": 5,                    
        "search_method": "hybrid",              
        "weights": {                   
            "tfidf": 0.3,
            "bm25": 0.3,
            "embeddings": 0.4
        }
    }
    """
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Query is required'}), 400
    
    query = data['query']
    top_n = data.get('top_n', TOP_N_RESULTS)
    search_method = data.get('search_method', None)
    
    logger.info(f"Search request received for query: '{query}', method: {search_method or 'default'}")
    
    # Search both databases
    satim_results = satim_search.search(query, top_n, search_method=search_method)
    intl_results = intl_search.search(query, top_n, search_method=search_method)
    
    return jsonify({
        'satim_results': [
            {'text': chunk, 'score': float(score)} 
            for chunk, score in satim_results
        ],
        'international_results': [
            {'text': chunk, 'score': float(score)} 
            for chunk, score in intl_results
        ],
        'query': query,
        'satim_count': len(satim_results),
        'international_count': len(intl_results),
        'method': search_method or DEFAULT_SEARCH_METHOD
    })

@api.route('/qa', methods=['POST', 'OPTIONS'])
@cross_origin()
def question_answer():
    """
    Question answering endpoint that performs comparative analysis
    """
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # Validate request
        data = request.json
        if not data or 'query' not in data:
            return jsonify({
                'answer': 'Query is required',
                'status': 'error',
                'metadata': {
                    'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    'user': 'user'
                }
            }), 400

        # Extract parameters
        query = data['query']
        user_id = data.get('user_id', 'anonymous')
        use_context = data.get('use_context', True)
        
        logger.info(f"QA request received for user '{user_id}', query: '{query}', use_context: {use_context}")

        # Get conversation history if needed
        conversation_history = None
        if use_context:
            conversation_history = conversation_manager.get_conversation(user_id)

        # Use generate_comparative_analysis instead of process_query
        analysis = qa_service.generate_comparative_analysis(query, conversation_history)

        # If query was rejected for security reasons
        if analysis.get('security_flag', False):
            return jsonify({
                'query': query,
                'answer': analysis['answer'],
                'status': 'rejected',
                'security_flag': True
            }), 403

        # Add the new messages to conversation history
        conversation_manager.add_message(user_id, 'user', query)
        conversation_manager.add_message(user_id, 'assistant', analysis['answer'])

        # Prepare response with safe access to optional fields
        response_data = {
            'query': query,
            'answer': analysis['answer'],
            'status': analysis['status']
        }

        # Add context if available
        if 'context' in analysis:
            response_data['context'] = {
                'satim': analysis['context'].get('satim', []),
                'international': analysis['context'].get('international', [])
            }

        # Add scores if available
        if 'scores' in analysis:
            response_data['scores'] = {
                'satim': analysis['scores'].get('satim', []),
                'international': analysis['scores'].get('international', [])
            }

        # Add method and conversation history
        response_data['method'] = data.get('search_method', 'hybrid')
        response_data['conversation_history'] = conversation_manager.get_conversation(user_id)

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({
            'answer': '### Error\nAn error occurred while processing your request.',
            'status': 'error',
            'metadata': {
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'user': 'user'
            }
        }), 500
        
@api.route('/conversation', methods=['POST'])
def update_conversation():
    """
    Update the conversation cache for a user session.
    
    Expected JSON payload:
    {
        "user_id": "unique_user_id",
        "role": "user/assistant",
        "content": "message content"
    }
    """
    data = request.json
    if not data or 'user_id' not in data or 'role' not in data or 'content' not in data:
        return jsonify({'error': 'Invalid payload'}), 400

    user_id = data['user_id']
    role = data['role']
    content = data['content']

    # Add message to conversation manager
    conversation_manager.add_message(user_id, role, content)

    return jsonify({
        'status': 'success', 
        'conversation': conversation_manager.get_conversation(user_id)
    }), 200

@api.route('/conversation/<user_id>', methods=['GET'])
def get_conversation(user_id):
    """
    Retrieve the conversation cache for a user session.
    """
    return jsonify({
        'conversation': conversation_manager.get_conversation(user_id)
    }), 200

@api.route('/conversation/<user_id>', methods=['DELETE'])
def clear_conversation(user_id):
    """
    Clear the conversation history for a user.
    """
    conversation_manager.clear_conversation(user_id)
    return jsonify({'status': 'success', 'message': 'Conversation cleared'}), 200

@api.route('/config', methods=['GET'])
def get_config():
    """Get current search configuration"""
    return jsonify({
        'weights': {
            'tfidf': TFIDF_WEIGHT,
            'bm25': BM25_WEIGHT,
            'embeddings': EMBEDDING_WEIGHT
        },
        'embedding_model': EMBEDDING_MODEL,
        'current_weights': {
            'satim': satim_search.vectorizer.weights,
            'international': intl_search.vectorizer.weights
        },
        'search_method': {
            'satim': satim_search.search_method,
            'international': intl_search.search_method
        },
        'available_methods': ['hybrid', 'tfidf', 'bm25', 'embeddings'],
        'conversation_settings': {
            'max_length': MAX_CONVERSATION_LENGTH,
            'expiry_time': CONVERSATION_EXPIRY_TIME
        }
    })

@api.route('/config', methods=['POST'])
def update_config():
    """Update search configuration for both services"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No configuration data provided'}), 400
    
    try:
        # Update search method if provided
        search_method = data.get('search_method')
        if search_method:
            satim_search.set_search_method(search_method)
            intl_search.set_search_method(search_method)
            logger.info(f"Search method updated to: {search_method}")
            
        # Update weights if provided
        weights = data.get('weights', {})
        if weights:
            tfidf = float(weights.get('tfidf', TFIDF_WEIGHT))
            bm25 = float(weights.get('bm25', BM25_WEIGHT))
            embeddings = float(weights.get('embeddings', EMBEDDING_WEIGHT))
            
            satim_search.vectorizer.set_weights(
                tfidf_weight=tfidf,
                bm25_weight=bm25,
                embedding_weight=embeddings
            )
            intl_search.vectorizer.set_weights(
                tfidf_weight=tfidf,
                bm25_weight=bm25,
                embedding_weight=embeddings
            )
            
            logger.info(f"Search weights updated for both services")
            
        return jsonify({
            'weights': {
                'satim': satim_search.vectorizer.weights,
                'international': intl_search.vectorizer.weights
            },
            'search_method': {
                'satim': satim_search.search_method,
                'international': intl_search.search_method
            },
            'status': 'updated'
        })
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return jsonify({'error': str(e)}), 500