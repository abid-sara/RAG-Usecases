"""Conversation Context Manager for maintaining chat history"""

import time
from collections import defaultdict

class ConversationManager:
    def __init__(self, max_conversation_length=10, expiry_time=3600):
        """
        Initialize the conversation manager
        
        Args:
            max_conversation_length (int): Maximum number of messages to keep in history
            expiry_time (int): Time in seconds after which a conversation expires
        """
        self.conversations = defaultdict(list)
        self.last_activity = defaultdict(float)
        self.max_conversation_length = max_conversation_length
        self.expiry_time = expiry_time
    
    def add_message(self, user_id, role, content):
        """
        Add a message to the conversation history
        
        Args:
            user_id (str): Unique identifier for the user
            role (str): Either 'user' or 'assistant'
            content (str): The message content
        """
        # Clean expired conversations first
        self._clean_expired_conversations()
        
        # Add the new message
        self.conversations[user_id].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        
        # Update last activity time
        self.last_activity[user_id] = time.time()
        
        # Trim conversation if it exceeds max length
        if len(self.conversations[user_id]) > self.max_conversation_length:
            self.conversations[user_id] = self.conversations[user_id][-self.max_conversation_length:]
    
    def get_conversation(self, user_id):
        """
        Get the conversation history for a user
        
        Args:
            user_id (str): Unique identifier for the user
            
        Returns:
            list: List of conversation messages
        """
        # Clean expired conversations first
        self._clean_expired_conversations()
        
        # Return the conversation without timestamps
        return [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in self.conversations.get(user_id, [])
        ]
    
    def _clean_expired_conversations(self):
        """Remove expired conversations to free up memory"""
        current_time = time.time()
        expired_users = [
            user_id for user_id, last_time in self.last_activity.items()
            if current_time - last_time > self.expiry_time
        ]
        
        for user_id in expired_users:
            del self.conversations[user_id]
            del self.last_activity[user_id]
    
    def clear_conversation(self, user_id):
        """
        Clear the conversation history for a user
        
        Args:
            user_id (str): Unique identifier for the user
        """
        if user_id in self.conversations:
            del self.conversations[user_id]
            del self.last_activity[user_id]