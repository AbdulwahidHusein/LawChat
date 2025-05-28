"""
Configuration settings for the Ethiopian LawChat application.

This module contains all configuration constants, API settings, and 
application parameters used throughout the system.
"""

import os

# API Configuration
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = "test-index"
PINECONE_HOST = "https://test-index-t9390q6.svc.aped-4627-b74a.pinecone.io"

# OpenAI Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
MAX_CONTEXT_LENGTH = 8000
TOP_K = 3

# Performance Optimization
ENABLE_CACHING = True
CACHE_TTL = 300
MIN_QUERY_LENGTH = 3
MAX_QUERY_LENGTH = 500

# Streamlit Configuration
PAGE_CONFIG = {
    "page_title": "Ethiopian LawChat",
    "page_icon": "⚖️",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "menu_items": {
        'Get Help': 'https://github.com/your-repo/lawchat',
        'Report a bug': "mailto:your-email@example.com",
        'About': "# Ethiopian LawChat\nAI-powered legal research assistant for Ethiopian law."
    }
}

# UI Configuration
MAX_SOURCES_DISPLAY = 9
SOURCE_PREVIEW_LENGTH = 200
CHAT_HISTORY_LIMIT = 10
CONVERSATION_CONTEXT_LIMIT = 6 