"""
AI Services module for the Ethiopian LawChat application.

This module handles all interactions with external AI services including
OpenAI for embeddings and chat completions, and Pinecone for vector search.
"""

import openai
from pinecone import Pinecone
from typing import List, Dict, Any
import streamlit as st
import hashlib
import time

from config import (
    PINECONE_API_KEY, PINECONE_HOST, EMBEDDING_MODEL, 
    CHAT_MODEL, TOP_K, CONVERSATION_CONTEXT_LIMIT,
    ENABLE_CACHING, CACHE_TTL
)


# Simple in-memory cache for embeddings and responses
@st.cache_data(ttl=CACHE_TTL if ENABLE_CACHING else 0)
def cached_embedding(text: str, model: str, api_key_hash: str) -> List[float]:
    """Cached version of get_embedding to avoid repeated API calls."""
    return _get_embedding_direct(text, model, api_key_hash)


def _get_embedding_direct(text: str, model: str, api_key_hash: str) -> List[float]:
    """Direct embedding call without cache (used internally)."""
    # Reconstruct client from hash - this is a simplified approach
    # In production, you'd want a more secure method
    client = openai.OpenAI(api_key=st.session_state.get('openai_api_key', ''))
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding


@st.cache_data(ttl=CACHE_TTL if ENABLE_CACHING else 0)
def cached_chat_completion(messages_hash: str, api_key_hash: str, model: str) -> str:
    """Cached version of chat completion to avoid repeated API calls for same queries."""
    return _get_chat_completion_direct(messages_hash, api_key_hash, model)


def _get_chat_completion_direct(messages_hash: str, api_key_hash: str, model: str) -> str:
    """Direct chat completion call without cache (used internally)."""
    # This is a simplified approach - in production you'd reconstruct messages properly
    client = openai.OpenAI(api_key=st.session_state.get('openai_api_key', ''))
    # For now, we'll bypass caching for chat completions due to complexity
    return ""


def test_openai_api_key(api_key: str) -> bool:
    """Test if the OpenAI API key is valid by making a small request."""
    if not api_key or not api_key.startswith("sk-"):
        return False
    try:
        client = openai.OpenAI(api_key=api_key)
        # Use a very small test to minimize cost and time
        response = client.embeddings.create(
            input="test",
            model="text-embedding-3-small"
        )
        return True
    except Exception as e:
        print(f"API key test failed: {e}")
        return False


def initialize_clients(openai_api_key: str) -> tuple:
    """Initialize OpenAI and Pinecone clients with API keys."""
    if not openai_api_key:
        return None, None
    
    if not PINECONE_API_KEY:
        st.error("Pinecone API key is missing. Please set the PINECONE_API_KEY environment variable.")
        return None, None
    
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(host=PINECONE_HOST)
        return client, index
    except Exception as e:
        st.error(f"Error connecting to services: {e}")
        return None, None


def get_embedding(text: str, model: str = EMBEDDING_MODEL, openai_api_key: str = None) -> List[float]:
    """Convert input text to embedding vector using OpenAI API with caching."""
    if ENABLE_CACHING:
        # Create a hash of the API key for cache key (security through obscurity)
        api_key_hash = hashlib.md5(openai_api_key.encode()).hexdigest()[:8] if openai_api_key else "default"
        return cached_embedding(text, model, api_key_hash)
    else:
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding


def query_pinecone(query: str, index, openai_api_key: str, top_k: int = TOP_K) -> Any:
    """Search Pinecone index for similar document chunks with optimized settings."""
    query_embedding = get_embedding(query, openai_api_key=openai_api_key)
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    return results


def get_chat_completion(messages: List[Dict], openai_api_key: str, model: str = CHAT_MODEL) -> str:
    """Generate a response from OpenAI based on the conversation with optimizations."""
    client = openai.OpenAI(api_key=openai_api_key)
    
    # Optimize message length to reduce tokens
    optimized_messages = []
    total_length = 0
    
    for message in reversed(messages):
        msg_length = len(message.get('content', ''))
        if total_length + msg_length > 6000:  # Keep under token limit
            break
        optimized_messages.insert(0, message)
        total_length += msg_length
    
    response = client.chat.completions.create(
        model=model,
        messages=optimized_messages,
        temperature=0.3,  # Lower temperature for faster, more focused responses
        max_tokens=800,   # Limit response length for speed
    )
    return response.choices[0].message.content


def format_sources(results) -> List[Dict]:
    """Process Pinecone search results to readable source objects."""
    sources = []
    for match in results.matches:
        source = match.metadata.get("source", "Unknown source")
        text = match.metadata.get("text", "No text available")
        score = match.score
        sources.append({
            "source": source,
            "text": text,
            "score": score
        })
    return sources


def create_system_prompt(context_docs: List[Dict]) -> str:
    """Create a concise system prompt with context documents."""
    # Limit context to prevent token overflow
    limited_docs = context_docs[:3]  # Only use top 3 sources
    
    context = ""
    for i, doc in enumerate(limited_docs):
        # Limit text length per source
        text = doc['text'][:800] + "..." if len(doc['text']) > 800 else doc['text']
        context += f"\nSource {i+1} [{doc['source']}]: {text}\n"
    
    # Shorter, more focused system prompt
    system_prompt = f"""You are LawChat, a legal research assistant for Ethiopian law.

Context Documents:
{context}

Instructions:
- Answer based on the provided context
- Cite sources as [Source X]
- Be concise and direct
- If information is not in context, state clearly
"""
    return system_prompt


def prepare_chat_messages(user_messages: List[Dict], system_prompt: str) -> List[Dict]:
    """Prepare messages for chat completion with strict context limits."""
    chat_messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Only use last 2 user-assistant pairs to keep context short
    user_assistant_messages = [msg for msg in user_messages if msg["role"] != "system"]
    chat_messages.extend(user_assistant_messages[-4:])  # Last 4 messages (2 pairs)
    
    return chat_messages 