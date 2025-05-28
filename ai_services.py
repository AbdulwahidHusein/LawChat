"""
AI Services module for the Ethiopian LawChat application.

This module handles all interactions with external AI services including
OpenAI for embeddings and chat completions, and Pinecone for vector search.
"""

import openai
from pinecone import Pinecone
from typing import List, Dict, Any
import streamlit as st

from config import (
    PINECONE_API_KEY, PINECONE_HOST, EMBEDDING_MODEL, 
    CHAT_MODEL, TOP_K, CONVERSATION_CONTEXT_LIMIT
)


def test_openai_api_key(api_key: str) -> bool:
    """Test if the OpenAI API key is valid by making a small request."""
    if not api_key or not api_key.startswith("sk-"):
        return False
    try:
        client = openai.OpenAI(api_key=api_key)
        # Make a minimal request to test the key
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
    
    client = openai.OpenAI(api_key=openai_api_key)
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    try:
        index = pc.Index(host=PINECONE_HOST)
        # Test the connection by getting stats
        stats = index.describe_index_stats()
        return client, index
    except Exception as e:
        st.error(f"Error connecting to Pinecone: {e}")
        return None, None


def get_embedding(text: str, model: str = EMBEDDING_MODEL, openai_api_key: str = None) -> List[float]:
    """Convert input text to embedding vector using OpenAI API."""
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding


def query_pinecone(query: str, index, openai_api_key: str, top_k: int = TOP_K) -> Any:
    """Search Pinecone index for similar document chunks."""
    query_embedding = get_embedding(query, openai_api_key=openai_api_key)
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    return results


def get_chat_completion(messages: List[Dict], openai_api_key: str, model: str = CHAT_MODEL) -> str:
    """Generate a response from OpenAI based on the conversation."""
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
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
    """Create a system prompt with context documents to guide the AI response."""
    # Join all context documents with source information
    context = ""
    for i, doc in enumerate(context_docs):
        context += f"\nSource {i+1} [{doc['source']}]: {doc['text']}\n"
    
    # Create the system prompt
    system_prompt = f"""You are LawChat, a helpful legal research assistant. 
        You have access to the following relevant legal documents:

        {context}

        Please use this context to answer the user's questions about legal matters.
        When you reference specific information from these sources, cite the source as [Source X].
        If the information is not in the provided context, acknowledge that and provide general legal information, 
        but make it clear that this is general information and not specific legal advice.
        Always maintain a professional, helpful tone and format your responses clearly.
        """
    return system_prompt


def prepare_chat_messages(user_messages: List[Dict], system_prompt: str) -> List[Dict]:
    """Prepare messages for chat completion with context limits."""
    chat_messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add conversation context (last N messages to avoid token limits)
    user_assistant_messages = [msg for msg in user_messages if msg["role"] != "system"]
    chat_messages.extend(user_assistant_messages[-CONVERSATION_CONTEXT_LIMIT:])
    
    return chat_messages 