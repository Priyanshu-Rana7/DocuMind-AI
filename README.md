# 🚀 DocuMind AI

> AI-powered document intelligence platform that extracts structured information from invoices using OCR and Large Language Models.

---

## 📖 Overview

DocuMind AI is an AI-powered SaaS platform that automates document understanding.

Instead of manually reading invoices, users upload a document and receive structured information such as:

- Invoice Number
- Vendor Details
- Invoice Date
- Due Date
- Line Items
- Taxes
- Total Amount
- Confidence Score

The platform combines OCR with Large Language Models to transform unstructured documents into machine-readable data.

---

## ✨ Features

- 📄 Upload invoice documents
- 🔍 OCR-based text extraction
- 🤖 AI-powered invoice understanding
- 📊 Confidence score visualization
- ⚡ FastAPI REST API
- 🎨 React + TypeScript frontend
- 🌙 Dark mode support
- 🧪 Automated testing
- 🧩 Modular provider architecture

---

## 🏗️ Architecture

```
React Frontend
       │
       ▼
 FastAPI Backend
       │
 ┌─────┴─────┐
 │           │
OCR      LLM Provider
 │           │
 └─────┬─────┘
       ▼
Invoice Service
       │
Repository Layer
       │
 Storage / Database
```

---

## 🛠️ Tech Stack

### Backend

- FastAPI
- Python
- EasyOCR
- OpenRouter
- Pydantic

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS

### Testing

- Pytest

### Version Control

- Git
- GitHub