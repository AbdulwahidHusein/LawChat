"""
Ethiopian LawChat - Main Application

A professional AI-powered legal research assistant for Ethiopian law.
This modular application uses RAG (Retrieval-Augmented Generation) to provide
accurate legal information with proper source attribution.

Author: LawChat Development Team
Version: 2.0
"""

import streamlit as st
import time
from typing import Optional

# Import modular components
from config import PAGE_CONFIG
from styles import MAIN_CSS
from ui_components import (
    apply_custom_styles, display_main_header, display_stats_cards,
    display_api_key_form, display_search_suggestions, display_quick_actions,
    display_chat_messages, display_sources_sidebar, display_document_info,
    display_search_history
)
from ai_services import (
    initialize_clients, query_pinecone, format_sources, 
    create_system_prompt, prepare_chat_messages, get_chat_completion
)
from session_manager import (
    initialize_session_state, get_openai_api_key, 
    add_message_to_history, increment_chat_count,
    update_last_sources, add_to_search_history
)
from search_features import get_suggested_questions, validate_query


def initialize_application():
    """Initialize the Streamlit application with configuration and styling."""
    st.set_page_config(**PAGE_CONFIG)
    apply_custom_styles()
    initialize_session_state()


def handle_api_key_validation() -> Optional[str]:
    """Handle API key input and validation."""
    openai_api_key = display_api_key_form()
    
    if not openai_api_key or not openai_api_key.startswith("sk-"):
        st.warning("🔑 Please enter a valid OpenAI API key to continue.")
        
        # Show helpful information while waiting for API key
        st.markdown("### 🚀 Getting Started")
        st.markdown("""
        1. **Get an OpenAI API Key**: Visit [OpenAI Platform](https://platform.openai.com/account/api-keys)
        2. **Enter your key** in the field above
        3. **Start asking questions** about Ethiopian law
        """)
        
        # Display sample questions even without API key
        st.markdown("### 💡 Example Questions You Can Ask:")
        examples = get_suggested_questions()
        for example in examples[:4]:
            st.markdown(f"• {example}")
        
        return None
    
    return openai_api_key


def setup_sidebar():
    """Setup the sidebar with all components."""
    with st.sidebar:
        st.markdown("# 🎛️ Control Panel")
        
        # Display document information
        display_document_info()
        
        # Display search history and get any repeated query
        repeated_query = display_search_history()
        
        # Display sources
        display_sources_sidebar(st.session_state.last_sources)
        
        return repeated_query


def process_user_query(user_input: str, index, openai_api_key: str):
    """Process a user query and generate AI response with optimizations."""
    start_time = time.time()
    
    # Validate the query
    if not validate_query(user_input):
        st.error("Please enter a valid question (at least 3 characters).")
        return
    
    # Check cache for similar recent queries to avoid duplicate API calls
    if 'query_cache' not in st.session_state:
        st.session_state.query_cache = {}
    
    # Simple cache key based on query
    cache_key = user_input.lower().strip()
    if cache_key in st.session_state.query_cache:
        cached_response = st.session_state.query_cache[cache_key]
        # Use cached response if it's less than 5 minutes old
        if time.time() - cached_response['timestamp'] < 300:
            st.info("⚡ Using cached response for similar recent query")
            add_message_to_history("assistant", cached_response['response'])
            update_last_sources(cached_response['sources'])
            return
    
    # Progress indicator for better UX
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Vector search
        status_text.text("🔍 Searching documents...")
        progress_bar.progress(25)
        
        results = query_pinecone(user_input, index, openai_api_key)
        sources = format_sources(results)
        update_last_sources(sources)
        
        # Step 2: Prepare context
        status_text.text("📝 Preparing context...")
        progress_bar.progress(50)
        
        system_prompt = create_system_prompt(sources)
        chat_messages = prepare_chat_messages(st.session_state.messages, system_prompt)
        
        # Step 3: Generate response
        status_text.text("🤖 Generating response...")
        progress_bar.progress(75)
        
        response = get_chat_completion(chat_messages, openai_api_key)
        
        # Step 4: Finalize
        status_text.text("✅ Complete!")
        progress_bar.progress(100)
        
        # Add to chat history
        add_message_to_history("assistant", response)
        add_to_search_history(user_input, response)
        
        # Cache the response
        st.session_state.query_cache[cache_key] = {
            'response': response,
            'sources': sources,
            'timestamp': time.time()
        }
        
        # Clean up cache if it gets too large
        if len(st.session_state.query_cache) > 10:
            oldest_key = min(st.session_state.query_cache.keys(), 
                           key=lambda k: st.session_state.query_cache[k]['timestamp'])
            del st.session_state.query_cache[oldest_key]
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        st.success(f"✅ Response generated in {response_time:.1f}s with {len(sources)} sources")
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Error processing query: {str(e)}")


def handle_query_input(index, openai_api_key: str, repeated_query: Optional[str] = None) -> bool:
    """Handle various query input methods and return True if query was processed."""
    query_processed = False
    
    # Check for suggested query
    suggested_query = display_search_suggestions()
    if suggested_query:
        add_message_to_history("user", suggested_query)
        increment_chat_count()
        process_user_query(suggested_query, index, openai_api_key)
        query_processed = True
    
    # Check for repeated query from sidebar (passed as parameter)
    elif repeated_query:
        add_message_to_history("user", repeated_query)
        increment_chat_count()
        process_user_query(repeated_query, index, openai_api_key)
        query_processed = True
    
    # Handle direct chat input
    else:
        user_input = st.chat_input(
            "💬 Ask anything about Ethiopian law...",
            key="main_chat_input"
        )
        
        if user_input:
            add_message_to_history("user", user_input)
            increment_chat_count()
            process_user_query(user_input, index, openai_api_key)
            query_processed = True
    
    return query_processed


def main():
    """Main application entry point."""
    # Initialize application
    initialize_application()
    
    # Display header and statistics
    display_main_header()
    display_stats_cards()
    
    # Handle API key validation
    openai_api_key = handle_api_key_validation()
    if not openai_api_key:
        return
    
    # Initialize AI clients
    client, index = initialize_clients(openai_api_key)
    if not client or not index:
        st.error("❌ Failed to initialize AI services. Please check your API keys and try again.")
        return
    
    # Setup sidebar (this also returns any repeated query)
    repeated_query = setup_sidebar()
    
    # Display quick actions
    display_quick_actions()
    
    # Handle query input and processing (pass the repeated query)
    query_processed = handle_query_input(index, openai_api_key, repeated_query)
    
    # Display chat messages
    display_chat_messages(st.session_state.messages)
    
    # If a query was processed, rerun to show updated UI
    if query_processed:
        st.rerun()


if __name__ == "__main__":
    main() 