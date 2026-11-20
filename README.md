# AI Customer Support Agent

An AI-powered customer support system built with **Python, FastAPI, PostgreSQL, RAG, Local LLMs, and Telegram Bot API**.

The project aims to develop an intelligent customer support agent capable of answering customer questions using a knowledge base, retrieving customer and order information, and executing basic tools through an AI agent architecture.

---

## 🚀 Project Overview

This project combines backend engineering with modern AI technologies to build a modular customer support system.

### Key Features

- REST API built with FastAPI.
- PostgreSQL database for customer, message, and order management.
- Telegram bot integration for customer communication.
- Retrieval-Augmented Generation (RAG) for knowledge retrieval.
- Local LLM integration using Ollama.
- AI agent with basic tool-calling functionality.
- Database-backed order lookup.
- Lightweight C++ text preprocessing component.

---

## 🛠️ Technologies & Tools

| Category | Technologies |
|---|---|
| Programming Languages | Python, C++ |
| Backend Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| AI / LLM | Ollama, Qwen 2.5 (3B) |
| RAG | ChromaDB |
| Embeddings | Sentence Transformers |
| Bot Integration | Telegram Bot API |
| HTTP Client | HTTPX |
| C++ Integration | C++ Preprocessor |
| Version Control | Git & GitHub |

---

# 📌 Development Roadmap

## Part 1: Backend Development

### 1. Backend & Project Setup

**Status: Completed**

- Python environment setup
- FastAPI installation and configuration
- Modular project structure
- Git & GitHub setup

### 2. Database & CRUD Operations

**Status: Completed**

- PostgreSQL configuration
- SQLAlchemy integration
- Database models
- Customer and Message entities
- CRUD operations
- Database connection management

### 3. Telegram Bot Integration

**Status: Completed**

- Telegram Bot API integration
- FastAPI integration
- Incoming and outgoing messages
- Message logging in PostgreSQL
- Basic error handling
- Integration testing

---

## Part 2: Artificial Intelligence

### 4. Knowledge Base & RAG

**Status: Completed**

- PDF and TXT document processing
- Text extraction and chunking
- Text embeddings
- ChromaDB vector database
- Semantic search
- Basic RAG pipeline
- Initial retrieval testing

**Initial Test:**

Successfully processed a TXT document, generated a text chunk, stored it in ChromaDB, and retrieved relevant information using semantic search.

### 5. LLM Integration

**Status: Implemented**

- Ollama local LLM setup
- Qwen 2.5 (3B) model integration
- Prompt engineering
- Context injection
- Response generation
- Grounded answers using retrieved knowledge
- FastAPI AI endpoint

### 6. AI Agent & Tool Calling

**Status: Basic Implementation**

- Function calling architecture
- Order lookup tool
- Customer information lookup functionality
- Basic agent decision-making
- Tool execution
- Database-backed order retrieval

The objective is to enable the AI agent to retrieve real customer and order information instead of relying only on generated responses.

---

## Part 3: C++ Integration

### 7. Lightweight C++ Component

**Status: Initial Implementation**

A small C++ component has been introduced into the existing Python-based project.

- C++ text preprocessing
- Separate C++ source file
- Python integration through a dedicated preprocessing module
- Compiled C++ component
- Lightweight implementation without changing the existing backend architecture

The purpose is to demonstrate basic integration between Python and C++ while keeping the main application Python-based.

---

## 📂 Project Structure

```text
AI-Customer-Support-Agent/
│
├── app/
│   ├── ai/
│   │   ├── agent.py
│   │   ├── llm.py
│   │   ├── prompts.py
│   │   ├── routes.py
│   │   └── tools.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── dependencies.py
│   │   └── models.py
│   │
│   ├── knowledge_base/
│   │   ├── document_loader.py
│   │   ├── rag_pipeline.py
│   │   ├── text_splitter.py
│   │   ├── vector_store.py
│   │   │
│   │   └── ccp/
│   │       ├── cpp_preprocessor.py
│   │       └── text_preprocessor.cpp
│   │
│   ├── retrieval/
│   │   └── retriever.py
│   │
│   ├── telegram/
│   │   └── bot.py
│   │
│   ├── tools/
│   │   └── order_lookup.py
│   │
│   └── main.py
│
├── chroma_db/
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/ardalan-farkhondeh/AI-Customer-Support-Agent.git

cd AI-Customer-Support-Agent
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root.

Configure the required environment variables, including:

- PostgreSQL database connection
- Telegram bot token
- Internal API credentials
- Other application settings

**Note:** Never upload your `.env` file or API keys to GitHub.

### 5. Start PostgreSQL

Make sure PostgreSQL is installed and running, and the project database is configured.

### 6. Start Ollama

Install Ollama and download the required model:

```bash
ollama pull qwen2.5:3b
```

### 7. Run the FastAPI Application

```bash
uvicorn app.main:app --reload
```

Open the API documentation:

http://127.0.0.1:8000/docs

---

## 🧪 Testing

The project has been tested incrementally during development.

- FastAPI endpoints and CRUD operations
- PostgreSQL database operations
- Telegram incoming and outgoing messages
- Database message logging
- RAG document processing and retrieval
- Semantic search functionality
- Local LLM response generation
- Grounded answers using knowledge base context
- Basic AI tool-calling functionality
- C++ preprocessing component

---

## 🎯 Future Improvements

- Complete AI agent integration with Telegram conversations
- Improve agent decision-making
- Expand customer and order management tools
- Human support handoff
- Improve error handling and logging
- AI response evaluation
- Docker containerization
- CI/CD pipeline
- Cloud deployment using AWS

---

## 👨‍💻 Author

**Ardalan Farkhondeh**

AI & Machine Learning | Deep Learning | Software Engineering

GitHub: [ardalan-farkhondeh](https://github.com/ardalan-farkhondeh)

---

## 📄 License

This project is developed for educational, experimental, and portfolio purposes.