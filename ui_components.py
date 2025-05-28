"""
UI Components module for the Ethiopian LawChat application.

This module contains all user interface components and display functions
for creating the modern, interactive interface.
"""

import streamlit as st
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import os

from config import SOURCE_PREVIEW_LENGTH, MAX_SOURCES_DISPLAY
from styles import MAIN_CSS


def apply_custom_styles():
    """Apply custom CSS styles to the application."""
    st.markdown(MAIN_CSS, unsafe_allow_html=True)


def display_main_header():
    """Display the main application header with gradient background."""
    st.markdown("""
    <div class="main-header">
        <div class="main-title">⚖️ Ethiopian LawChat</div>
        <div class="main-subtitle">AI-Powered Legal Research Assistant</div>
    </div>
    """, unsafe_allow_html=True)


def display_stats_cards():
    """Display session statistics in attractive cards."""
    from session_manager import get_session_stats
    
    stats = get_session_stats()
    
    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats.get('queries', 0)}</div>
            <div class="stat-label">Queries Asked</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats.get('duration', '0m')}</div>
            <div class="stat-label">Session Time</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats.get('sources_found', 0)}</div>
            <div class="stat-label">Sources Found</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{stats.get('avg_response_time', '0s')}</div>
            <div class="stat-label">Avg Response</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def display_chat_messages(messages: List[Dict]):
    """Render chat messages with proper styling and formatting."""
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in messages:
        if message["role"] == "system":
            continue  # Don't display system messages
        
        if message["role"] == "user":
            avatar = "👤"
            class_name = "user"
        else:
            avatar = "⚖️"
            class_name = "assistant"
        
        # Process message content to highlight source references and format text
        content = message["content"]
        
        # Format paragraphs - split on double newlines and add proper spacing
        paragraphs = content.split('\n\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            # Clean up single newlines within paragraphs
            clean_paragraph = paragraph.replace('\n', ' ').strip()
            if clean_paragraph:
                formatted_paragraphs.append(clean_paragraph)
        
        # Join paragraphs with proper HTML breaks
        content = '<br><br>'.join(formatted_paragraphs)
        
        # Highlight source references like [Source X]
        for i in range(1, MAX_SOURCES_DISPLAY + 1):
            source_tag = f"[Source {i}]"
            if source_tag in content:
                content = content.replace(
                    source_tag, 
                    f'<span class="source-reference">{source_tag}</span>'
                )
        
        st.markdown(f"""
        <div class="chat-message {class_name}">
            <div class="avatar">{avatar}</div>
            <div class="message">{content}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def display_sources_sidebar(sources: List[Dict]):
    """Display source documents in the sidebar with expandable details."""
    st.sidebar.markdown("## 📚 Source Documents")
    
    if not sources:
        st.sidebar.info("No source documents available yet. Ask a question to see relevant sources!")
        return
    
    st.sidebar.markdown(f"Found **{len(sources)}** relevant sources:")
    
    for i, source in enumerate(sources):
        with st.sidebar.expander(f"📄 Source {i+1}: {source['source']}", expanded=False):
            # Show relevance score
            st.markdown(f"**Relevance Score:** {source['score']:.4f}")
            
            # Show preview of text
            preview = source['text']
            if len(preview) > SOURCE_PREVIEW_LENGTH:
                preview = preview[:SOURCE_PREVIEW_LENGTH] + "..."
            
            st.markdown("**Preview:**")
            st.markdown(f"_{preview}_")
            
            # Show full text in a simple text area
            st.markdown("**Full Text:**")
            st.text_area(
                label="Full content",
                value=source['text'],
                height=150,
                key=f"source_text_{i}_{len(source['text'])}",
                label_visibility="collapsed"
            )


def display_api_key_form() -> str:
    """Display form for entering the OpenAI API key."""
    from ai_services import test_openai_api_key
    
    # Check if the API key is already in the session state
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = ""
    
    # Check environment variable first
    env_api_key = os.environ.get("OPENAI_API_KEY", "")
    if env_api_key and not st.session_state.openai_api_key:
        st.session_state.openai_api_key = env_api_key
    
    st.markdown('<div class="api-key-container">', unsafe_allow_html=True)
    st.markdown('<div class="api-key-header">🔑 OpenAI API Key</div>', unsafe_allow_html=True)
    
    # Input field for the API key
    api_key = st.text_input(
        "Enter your OpenAI API key:",
        type="password",
        value=st.session_state.openai_api_key,
        key="api_key_input",
        help="Your API key will be stored only in this session and not saved permanently. Must start with 'sk-'.",
    )
    
    col1, col2 = st.columns([1, 3])
    # Save button
    with col1:
        if st.button("Save & Verify", key="save_api_key"):
            if api_key and api_key.startswith("sk-"):
                # Test the key before saving
                if test_openai_api_key(api_key):
                    st.session_state.openai_api_key = api_key
                    st.success("✅ API key verified and saved for this session!")
                else:
                    st.error("❌ Invalid API key. Please check and try again.")
            else:
                st.error("❌ Please enter a valid OpenAI API key (must start with 'sk-').")
    
    with col2:
        st.markdown("""
        <div style="padding: 10px; font-size: 0.85em; color: #555;">
        Need an API key? <a href="https://platform.openai.com/account/api-keys" target="_blank">Get one from OpenAI</a>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return st.session_state.openai_api_key


def display_search_suggestions() -> Optional[str]:
    """Display clickable search suggestions."""
    from search_features import get_suggested_questions
    
    suggestions = get_suggested_questions()
    
    st.markdown('<div class="search-suggestions">', unsafe_allow_html=True)
    st.markdown("💡 **Try asking about:**", unsafe_allow_html=True)
    
    # Create a grid of suggestion chips
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            # Create unique key using index and hash of suggestion
            unique_key = f"suggestion_{i}_{hash(suggestion) % 10000}"
            if st.button(suggestion, key=unique_key, help="Click to use this question"):
                return suggestion
    
    st.markdown('</div>', unsafe_allow_html=True)
    return None


def display_quick_actions():
    """Display quick action buttons."""
    st.markdown('<div class="quick-actions">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Search Tips", help="Get tips for better searches"):
            st.info("""
            **Search Tips:**
            - Be specific: "theft penalty" instead of "crime"
            - Ask about specific rights: "freedom of speech"
            - Use legal terms when possible
            - Ask follow-up questions for clarity
            """)
    
    with col2:
        if st.button("📊 Export Chat", help="Export current conversation"):
            chat_export = "\n".join([
                f"{msg['role'].title()}: {msg['content']}" 
                for msg in st.session_state.messages 
                if msg['role'] != 'system'
            ])
            st.download_button(
                label="💾 Download Chat",
                data=chat_export,
                file_name=f"lawchat_session_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
    
    with col3:
        if st.button("🔄 Clear History", help="Clear chat history"):
            if st.button("✅ Confirm Clear", key="confirm_clear"):
                from session_manager import clear_session_data
                clear_session_data()
                st.rerun()
    
    with col4:
        if st.button("ℹ️ About", help="Learn about this system"):
            st.info("""
            **Ethiopian LawChat v2.0**
            
            An AI-powered legal research assistant using:
            - 🤖 OpenAI GPT-4 for intelligent responses
            - 🔍 Vector search for relevant document retrieval
            - 📚 Ethiopian legal documents (Constitution & Criminal Code)
            - 🎯 Source attribution for transparency
            
            Built with Streamlit, Pinecone, and OpenAI.
            """)
    
    st.markdown('</div>', unsafe_allow_html=True)


def display_document_info():
    """Display document information in sidebar."""
    from data_manager import get_document_info
    
    doc_info = get_document_info()
    
    st.sidebar.markdown("## 📚 Document Library")
    st.sidebar.markdown(f"""
    - **Documents:** {doc_info['documents']} legal texts
    - **Text Chunks:** {doc_info['chunks']} searchable segments
    - **Last Updated:** {doc_info['last_updated'][:10] if isinstance(doc_info['last_updated'], str) and len(doc_info['last_updated']) > 10 else doc_info['last_updated']}
    """)
    
    # Document list
    with st.sidebar.expander("📋 Available Documents", expanded=False):
        st.markdown("""
        1. **Ethiopian Constitution** (English)
           - Fundamental rights and freedoms
           - Government structure
           - Constitutional principles
        
        2. **Ethiopian Criminal Code**
           - Criminal offenses and penalties
           - Legal procedures
           - Justice system
        """)


def display_search_history() -> Optional[str]:
    """Display recent search history in sidebar."""
    if not st.session_state.search_history:
        return None
    
    st.sidebar.markdown("## 📜 Recent Searches")
    
    for i, search in enumerate(reversed(st.session_state.search_history[-5:])):
        with st.sidebar.expander(f"🔍 {search['timestamp']}", expanded=False):
            st.markdown(f"**Query:** {search['query']}")
            if search.get('preview'):
                st.markdown(f"**Response:** {search['preview']}")
            # Create unique key using index and hash of query
            unique_key = f"research_{i}_{hash(search['query']) % 10000}"
            if st.button("🔄 Search Again", key=unique_key):
                return search['query']
    
    return None


def show_loading_states():
    """Display loading animations during processing."""
    with st.spinner("🔍 Searching through legal documents..."):
        st.empty()  # Placeholder for search progress
    
    with st.spinner("✍️ Generating comprehensive legal analysis..."):
        st.empty()  # Placeholder for generation progress 