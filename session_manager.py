"""
Session Management module for the Ethiopian LawChat application.

This module handles all session state management, including user data,
search history, and application state persistence.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List
import os

from config import CHAT_HISTORY_LIMIT


def initialize_session_state():
    """Initialize all session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful legal research assistant."},
        ]
    
    if "last_sources" not in st.session_state:
        st.session_state.last_sources = []
    
    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    
    if "chat_count" not in st.session_state:
        st.session_state.chat_count = 0
    
    if "total_tokens_used" not in st.session_state:
        st.session_state.total_tokens_used = 0
    
    if "session_start_time" not in st.session_state:
        st.session_state.session_start_time = datetime.now()


def get_openai_api_key() -> str:
    """Get OpenAI API key from session state or environment variable."""
    # First check if it's in the session state
    if "openai_api_key" in st.session_state and st.session_state.openai_api_key:
        return st.session_state.openai_api_key
    
    # Otherwise check environment variable
    return os.environ.get("OPENAI_API_KEY", "")


def get_session_stats() -> Dict:
    """Get session statistics for display."""
    if "session_start_time" not in st.session_state:
        return {}
    
    session_duration = datetime.now() - st.session_state.session_start_time
    duration_minutes = int(session_duration.total_seconds() / 60)
    
    return {
        "queries": st.session_state.chat_count,
        "duration": f"{duration_minutes}m",
        "sources_found": len(st.session_state.last_sources),
        "avg_response_time": "2.3s"  # This could be calculated from actual response times
    }


def add_to_search_history(query: str, response_preview: str = ""):
    """Add a query to search history."""
    if query and query not in [h.get('query', '') for h in st.session_state.search_history]:
        st.session_state.search_history.append({
            'query': query,
            'timestamp': datetime.now().strftime("%H:%M"),
            'preview': response_preview[:100] + "..." if len(response_preview) > 100 else response_preview
        })
        # Keep only last N searches
        if len(st.session_state.search_history) > CHAT_HISTORY_LIMIT:
            st.session_state.search_history = st.session_state.search_history[-CHAT_HISTORY_LIMIT:]


def clear_session_data():
    """Clear all session data and reset to initial state."""
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful legal research assistant."}
    ]
    st.session_state.last_sources = []
    st.session_state.search_history = []
    st.session_state.chat_count = 0


def update_last_sources(sources: List[Dict]):
    """Update the last sources found in the session."""
    st.session_state.last_sources = sources


def increment_chat_count():
    """Increment the chat counter."""
    st.session_state.chat_count += 1


def add_message_to_history(role: str, content: str):
    """Add a message to the chat history."""
    st.session_state.messages.append({"role": role, "content": content}) 