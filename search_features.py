"""
Search Features module for the Ethiopian LawChat application.

This module handles search suggestions, query processing, and search-related
functionality to enhance the user experience.
"""

import streamlit as st
from typing import List


def get_suggested_questions() -> List[str]:
    """Get context-aware suggested questions."""
    base_suggestions = [
        "What are the fundamental rights in the Ethiopian Constitution?",
        "What is the penalty for theft under Ethiopian law?",
        "How does Ethiopian law define citizenship?",
        "What are the powers of the federal government?",
        "What criminal penalties exist for corruption?",
        "How are human rights protected in Ethiopia?",
        "What is the structure of the Ethiopian judicial system?",
        "What are the language rights in Ethiopia?",
        "How does the Constitution address freedom of expression?",
        "What are the requirements for Ethiopian nationality?"
    ]
    
    # If there's recent search history, suggest related questions
    if st.session_state.search_history:
        recent_queries = st.session_state.search_history[-3:]
        # In a more advanced version, we could use AI to generate related questions
        # For now, return a mix of base suggestions
        return base_suggestions[:6]
    
    return base_suggestions[:6]


def validate_query(query: str) -> bool:
    """Validate if a user query is appropriate and well-formed."""
    if not query or len(query.strip()) < 3:
        return False
    
    # Add any additional validation logic here
    return True


def enhance_query(query: str) -> str:
    """Enhance a user query for better search results."""
    # Basic query enhancement - could be expanded with more sophisticated NLP
    query = query.strip()
    
    # Add context hints for better legal search
    legal_keywords = ["law", "legal", "constitution", "criminal", "code", "article", "section"]
    if not any(keyword in query.lower() for keyword in legal_keywords):
        # This is a simple enhancement - in practice, this would be more sophisticated
        pass
    
    return query


def get_search_tips() -> List[str]:
    """Get search tips for better user queries."""
    return [
        "Be specific: 'theft penalty' instead of 'crime'",
        "Ask about specific rights: 'freedom of speech'",
        "Use legal terms when possible",
        "Ask follow-up questions for clarity",
        "Reference specific articles or sections when known",
        "Use context from previous questions"
    ] 