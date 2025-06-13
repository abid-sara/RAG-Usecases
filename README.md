# ENSIA-AI Group Project - Spring 2025

![ENSIA-AI Logo](/client/src/assets/images/logo.png)

## Overview

This project is a comprehensive Question Answering (QA) system developed for the Ministry of Higher Education and Scientific Research. It features a sophisticated backend powered by state-of-the-art language models and a sleek, responsive frontend interface. The system is specifically designed to handle Arabic language queries and provide relevant answers based on a corpus of government documents.

## Features

- 🗣️ **Arabic Support**: Fully supports Arabic language processing and responses
- 🌓 **Dark/Light Mode**: Customizable UI with smooth transitions
- 🔍 **Semantic Search**: Embedding-powered document retrieval for high accuracy
- 🧠 **Context-Aware Responses**: Generates answers based on retrieved content
- 🏛️ **Official Design**: Aligns with government styling and branding
- 📚 **Citation Support**: Includes source references for generated responses

## 🔧 Project Structure

```
group-project-spring-2025/
├── client/                    # React + TypeScript user-facing frontend
│   ├── src/
│   │   ├── components/        # UI components
│   │   │   ├── custom/        # Project-specific components
│   │   │   └── ui/            # Generic UI components
│   │   ├── pages/             # Application pages
│   │   ├── context/           # React context providers
│   │   ├── assets/            # Images and static resources
│   │   ├── lib/               # Utility functions
│   │   └── interfaces/        # TypeScript interfaces
│   ├── public/                # Static files
│   └── index.html             # HTML entry point

├── admin/              # JavaScript-based dashboard panel

├── rag_core/                  # Python backend RAG system
│   ├── app/
│   │   ├── api/               # API endpoints (Flask)
│   │   ├── services/          # Business logic and orchestration
│   │   ├── storage/           # Vector store interactions
│   │   ├── utils/             # Helper utilities
│   │   └── __init__.py
│   ├── config/                # App configuration
│   │   └── settings.py
│   ├── data/                  # Stored FAISS vectors and processed files
│   ├── run.py                 # Entry point for running the backend
│   └── requirements.txt       # Python dependencies

├── .env
├── .gitignore
└── README.md
```

## 🧠 Tech Stack

### Backend

- **Python**
- **Flask** (REST API framework)
- **FAISS** (Vector similarity search)

### Frontend

- **TypeScript** with **React** for the user interface
- **JavaScript** with **React** for the dashboard
- **CSS / SCSS**
- **HTML5**

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### 1. Clone the Repository

```bash
git clone https://github.com/ENSIA-AI/group-project-spring-2025.git
cd group-project-spring-2025
```

---

### 2. Set Up the Python Backend (RAG System)

```bash
cd rag_core

# Optional: Set up virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit the .env file as needed
```

---

### 3. Set Up the Frontend (React + TS)

```bash
cd ../client
npm install  # or yarn install
```

---

### 4. Set Up the Dashboard (Optional)

```bash
cd ../admin
npm install  # or yarn install
```

---

## 🧪 Running the Application

Before running the application, add an empty json file to store the data

```bash
mkdir data
echo ['"القرار 0"'] > data\final.json
```

### Backend

```bash
# From project root
cd rag_core
python run.py
```

> App runs on: `http://localhost:5000`

---

### Frontend

```bash
# From project root
cd client
npm install
npm run dev  # or yarn dev
```

> App runs on: `http://localhost:3000`

---

### Dashboard (Optional)

```bash
# From project root
cd admin
npm install
npm start
```

---

## 👥 Team Members

- **Mohammed Abdelkhalek Benkiniouar**
- **Lyes Hadjar**
- **Sara Abid**
- **Rayane Lalam**
- **Mohamed Elamine Ali Zergaoui**

---

## 📄 License

This project is licensed for academic and governmental use by ENSIA-AI — All Rights Reserved.

---
