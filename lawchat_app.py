import os
import streamlit as st
import openai
from pinecone import Pinecone
from datetime import datetime
import textwrap
import uuid  # Add this for unique keys

# Configuration
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = "test-index"
PINECONE_HOST = "https://test-index-t9390q6.svc.aped-4627-b74a.pinecone.io"
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o"
MAX_CONTEXT_LENGTH = 12000  # Maximum context length for OpenAI model
TOP_K = 5  # Number of top similar vectors to retrieve

# Initialize Streamlit page with a nice clean look
st.set_page_config(
    page_title="Ethiopian LawChat",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for better UI
st.markdown("""
<style>
    /* Main background and container styling */
    .main {
        background-color: #fcfcfc;
        padding: 1rem;
    }
    
    /* Chat message styling with better contrast */
    .chat-container {
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    .chat-message.user {
        background-color: #E3F2FD;
        border-left: 5px solid #1976D2;
    }
    .chat-message.assistant {
        background-color: #FFFFFF;
        border-left: 5px solid #43A047;
    }
    .chat-message .avatar {
        font-size: 1.5rem;
        margin-right: 1rem;
        min-width: 30px;
        display: flex;
        align-items: center;
    }
    .chat-message .message {
        color: #212121;
        flex: 1;
    }
    
    /* Source reference styling */
    .source-reference {
        display: inline-block;
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 0 5px;
        margin: 0 2px;
        border-radius: 3px;
        font-weight: 500;
        cursor: pointer;
    }
    
    /* Source tooltip on hover */
    .source-tooltip {
        position: relative;
        display: inline-block;
    }
    .source-tooltip .tooltip-content {
        visibility: hidden;
        width: 300px;
        background-color: #f9f9f9;
        color: #333;
        text-align: left;
        border-radius: 6px;
        padding: 10px;
        position: absolute;
        z-index: 1000;
        bottom: 125%;
        left: 50%;
        margin-left: -150px;
        opacity: 0;
        transition: opacity 0.3s;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        border: 1px solid #ddd;
    }
    .source-tooltip:hover .tooltip-content {
        visibility: visible;
        opacity: 1;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f5f7f9;
    }
    .source-item {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
        border-left: 3px solid #4CAF50;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .source-item:hover {
        box-shadow: 0 3px 6px rgba(0,0,0,0.15);
    }
    .source-title {
        font-weight: bold;
        color: #1565C0;
        margin-bottom: 5px;
    }
    .source-preview {
        font-size: 0.9em;
        color: #424242;
        max-height: 100px;
        overflow-y: auto;
        padding: 5px;
        background-color: #f8f9fa;
        border-radius: 4px;
    }
    
    /* Loading indicators */
    .loading-message {
        text-align: center;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        background-color: #FFF8E1;
        border: 1px solid #FFE082;
        color: #FF8F00;
    }
    
    /* Streamlit component overrides */
    .stTextInput>div>div>input {
        background-color: white;
    }
    button[data-baseweb="tab"] {
        margin-right: 10px;
    }
    
    /* Fix for content width */
    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Full text container */
    .full-text-container {
        margin-top: 10px;
        border-top: 1px solid #eee;
        padding-top: 10px;
    }
    .full-text-toggle {
        color: #1976D2;
        cursor: pointer;
        font-size: 0.9em;
        margin-bottom: 5px;
        display: inline-block;
    }
    
    /* API key section */
    .api-key-container {
        padding: 15px;
        background-color: #f0f7ff;
        border-radius: 8px;
        margin-bottom: 20px;
        border: 1px solid #c9e0ff;
    }
    .api-key-header {
        font-weight: 600;
        margin-bottom: 10px;
        font-size: 1.1em;
        color: #1976D2;
    }
    .api-key-input {
        border: 1px solid #c9d6e2 !important;
        background-color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Test OpenAI API key validity
def test_openai_api_key(api_key):
    """Test if the OpenAI API key is valid by making a small request."""
    if not api_key or not api_key.startswith("sk-"):
        return False
    
    try:
        client = openai.OpenAI(api_key=api_key)
        # Make a minimal test request
        response = client.embeddings.create(
            input="Test",
            model="text-embedding-3-small"
        )
        return True
    except Exception as e:
        st.error(f"API key validation failed: {str(e)}")
        return False

# Get OpenAI API key from session state or environment
def get_openai_api_key():
    """Get OpenAI API key from session state or environment variable."""
    # First check if it's in the session state
    if "openai_api_key" in st.session_state and st.session_state.openai_api_key:
        return st.session_state.openai_api_key
    
    # Otherwise check environment variable
    return os.environ.get("OPENAI_API_KEY", "")

# Initialize OpenAI and Pinecone clients
def initialize_clients(openai_api_key):
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

# Get embeddings for a text
def get_embedding(text, model=EMBEDDING_MODEL, openai_api_key=None):
    """Convert input text to embedding vector using OpenAI API."""
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding

# Query Pinecone for similar documents
def query_pinecone(query, index, openai_api_key, top_k=TOP_K):
    """Search Pinecone index for similar document chunks."""
    query_embedding = get_embedding(query, openai_api_key=openai_api_key)
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    return results

# Create a chat completion with OpenAI
def get_chat_completion(messages, openai_api_key, model=CHAT_MODEL):
    """Generate a response from OpenAI based on the conversation."""
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content

# Format sources for display
def format_sources(results):
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

# Create a system prompt with context
def create_system_prompt(context_docs):
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

# Display chat messages
def display_chat_messages(messages):
    """Render chat messages with proper styling."""
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
        
        # Process message content to highlight source references
        content = message["content"]
        # Highlight source references like [Source X]
        for i in range(1, 10):  # Support up to 9 sources for simplicity
            source_tag = f"[Source {i}]"
            if source_tag in content:
                # If we have the source text available, create a tooltip
                tooltip = ""
                if "last_sources" in st.session_state and len(st.session_state.last_sources) >= i:
                    source_text = st.session_state.last_sources[i-1]["text"]
                    # Truncate long text for tooltip
                    if len(source_text) > 200:
                        source_text = source_text[:200] + "..."
                    tooltip = f'<div class="tooltip-content">{source_text}</div>'
                
                content = content.replace(
                    source_tag, 
                    f'<span class="source-reference source-tooltip">{source_tag}{tooltip}</span>'
                )
        
        st.markdown(f"""
        <div class="chat-message {class_name}">
            <div class="avatar">{avatar}</div>
            <div class="message">{content}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Display sources in sidebar
def display_sources_sidebar(sources):
    """Display source documents in the sidebar with expandable details."""
    st.sidebar.markdown("## Source Documents")
    
    if not sources:
        st.sidebar.info("No source documents available yet.")
        return
    
    # Create a session key for each source to avoid duplicates
    if "source_keys" not in st.session_state:
        st.session_state.source_keys = {}
    
    for i, source in enumerate(sources):
        # Generate a unique key for each source if it doesn't exist
        source_id = f"{source['source']}_{i}"
        if source_id not in st.session_state.source_keys:
            st.session_state.source_keys[source_id] = str(uuid.uuid4())
        
        unique_key = st.session_state.source_keys[source_id]
        
        with st.sidebar.expander(f"Source {i+1}: {source['source']}", expanded=False):
            # Show preview of text
            preview = source['text']
            if len(preview) > 300:
                preview = preview[:300] + "..."
            
            st.markdown(f"""
            <div class="source-item">
                <div class="source-title">Source {i+1}: {source['source']}</div>
                <div class="source-preview">{preview}</div>
                <div style="margin-top: 5px; font-size: 0.8em; color: #666;">Relevance: {source['score']:.4f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show full text without using nested expander
            st.markdown("<div class='full-text-container'>", unsafe_allow_html=True)
            st.markdown("<span class='full-text-toggle'>📄 Full Text:</span>", unsafe_allow_html=True)
            st.text_area(
                label=f"Source {i+1} Full Text",  # Provide a meaningful label
                value=source['text'],
                height=200,
                key=f"source_text_{unique_key}",
                label_visibility="hidden"  # Hide the label but keep it for accessibility
            )
            st.markdown("</div>", unsafe_allow_html=True)

# API key input form
def api_key_form():
    """Display form for entering the OpenAI API key."""
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

# Main application
def main():
    """Main application logic."""
    # Add a header
    st.markdown("<h1 style='text-align: center; margin-bottom: 1.5rem;'>LawChat <small>Legal Research Assistant</small></h1>", unsafe_allow_html=True)
    
    # Get OpenAI API key from form
    openai_api_key = api_key_form()
    
    # Check if API key is valid before initializing clients
    if not openai_api_key or not openai_api_key.startswith("sk-"):
        st.warning("Please enter a valid OpenAI API key to continue.")
        st.stop()  # Stop execution if no valid API key
    
    # Initialize clients with the provided OpenAI API key
    client, index = initialize_clients(openai_api_key)
    
    # If API key is not provided or invalid, show error and return
    if not client or not index:
        st.error("Failed to initialize. Please check your API keys and try again.")
        return
    
    # Initialize session state for chat history (but only once)
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": "You are a helpful legal research assistant."},
        ]
    
    if "last_sources" not in st.session_state:
        st.session_state.last_sources = []
    
    # Display sources in sidebar
    display_sources_sidebar(st.session_state.last_sources)
    
    # Main content area - chat messages
    display_chat_messages(st.session_state.messages)
    
    # Chat input
    user_input = st.chat_input("Ask a question about your legal documents...")
    
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display updated chat history
        display_chat_messages(st.session_state.messages)
        
        # Show a loading message while searching documents
        with st.spinner():
            st.markdown('<div class="loading-message">🔍 Searching through legal documents...</div>', unsafe_allow_html=True)
            
            # Query Pinecone for relevant documents
            results = query_pinecone(user_input, index, openai_api_key)
            
            # Format sources for display
            sources = format_sources(results)
            st.session_state.last_sources = sources
            
            # Create system prompt with context
            system_prompt = create_system_prompt(sources)
            
            # Prepare messages for chat completion
            chat_messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add the last few messages for conversation context
            # Skip system messages and only include user-assistant exchanges
            user_assistant_messages = [msg for msg in st.session_state.messages if msg["role"] != "system"]
            # Take only last 3 exchanges (6 messages) to avoid context length issues
            chat_messages.extend(user_assistant_messages[-6:])
        
        # Show a loading message while generating response
        with st.spinner():
            st.markdown('<div class="loading-message">✍️ Drafting a response based on the legal sources...</div>', unsafe_allow_html=True)
            
            # Get chat completion
            response = get_chat_completion(chat_messages, openai_api_key)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Refresh the page to show the updated chat
        st.rerun()

if __name__ == "__main__":
    main() 