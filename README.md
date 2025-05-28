# Ethiopian LawChat ⚖️

An AI-powered legal document Q&A system that helps users find relevant information from Ethiopian legal documents using advanced semantic search and GPT-4.

## 🌟 Features

- **Intelligent Q&A**: Ask questions about Ethiopian law in natural language
- **Semantic Search**: Advanced vector-based search using OpenAI embeddings
- **Source Attribution**: Every answer includes references to specific legal documents
- **Professional UI**: Clean, responsive Streamlit interface
- **Real-time Processing**: Fast retrieval from Pinecone vector database
- **Document Management**: Automatic PDF processing and indexing

## 📋 Currently Indexed Documents

- **Ethiopian Constitution** (English version)
- **Ethiopian Criminal Code**

## 🛠️ Technology Stack

- **Frontend**: Streamlit with custom CSS
- **AI Models**: OpenAI GPT-4 and text-embedding-3-small
- **Vector Database**: Pinecone
- **PDF Processing**: PyPDF2
- **Language**: Python 3.8+

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Pinecone API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd LawChat
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export PINECONE_API_KEY="your-pinecone-api-key"
   ```

5. **Process legal documents (first time only)**
   ```bash
   python process_pdfs_to_pinecone.py
   ```

6. **Run the application**
   ```bash
   streamlit run lawchat_app.py
   ```

## 📖 Usage

1. **Start the application** and navigate to the provided URL
2. **Enter your API keys** in the sidebar (if not set as environment variables)
3. **Ask questions** about Ethiopian law in the chat interface
4. **Review sources** in the sidebar to see which documents informed the answer

### Example Questions

- "What are the fundamental rights guaranteed by the Ethiopian Constitution?"
- "What is the penalty for theft under Ethiopian criminal law?"
- "How does the Constitution define citizenship?"

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PDF Documents │───▶│  Text Extraction │───▶│   Text Chunks   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Query    │───▶│   OpenAI GPT-4   │◀───│   Pinecone DB   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                         ▲
                                ▼                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Formatted      │◀───│   Answer with    │    │   Embeddings    │
│  Response       │    │   Sources        │    │   (Vectors)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
LawChat/
├── lawchat_app.py              # Main Streamlit application
├── process_pdfs_to_pinecone.py # PDF processing and indexing
├── requirements.txt            # Python dependencies
├── processed_files.json       # Tracking file for processed PDFs
├── docs/                      # Legal document storage
│   ├── ET_Criminal_Code.pdf
│   └── EthiopiaConstitution english.pdf
└── README.md                  # This file
```

## 🔧 Configuration

Key settings can be modified in the script headers:

- `CHUNK_SIZE`: Text chunk size for processing (default: 1000 characters)
- `TOP_K`: Number of relevant chunks to retrieve (default: 5)
- `MAX_CONTEXT_LENGTH`: Maximum context for GPT-4 (default: 12000)

## 🚧 Future Enhancements

- [ ] Add more Ethiopian legal documents (Civil Code, Commercial Code, etc.)
- [ ] Implement advanced chunking strategies (semantic chunking)
- [ ] Add multilingual support (Amharic)
- [ ] Include chat history persistence
- [ ] Add document filtering and advanced search
- [ ] Implement user authentication and usage analytics
- [ ] Add export functionality for answers and sources

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Ethiopian legal documents used with respect for public domain status
- OpenAI for GPT-4 and embedding models
- Pinecone for vector database services
- Streamlit for the web application framework

## 📞 Contact

For questions or suggestions, please open an issue in this repository.

---

**Note**: This system is for educational and research purposes. Always consult qualified legal professionals for official legal advice.
