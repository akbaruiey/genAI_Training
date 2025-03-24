# AI Question Bank Generator with RAG

## Overview
This project is an AI-powered question bank generator using **Gradio**, **LangChain**, **Ollama embeddings**, and **Chroma vector database**. It allows users to:
- Upload **PDF documents**
- Generate **MCQs, True/False, Short Answer, and Long Answer questions**
- View and manage a **question bank**
- Create **exam papers** from stored questions

## Features
- **PDF Upload & Processing**: Extracts text and stores vectorized representations
- **AI-based Question Generation**: Uses a **Retrieval-Augmented Generation (RAG)** approach
- **Categorized Question Display**: Displays questions in an **accordion UI** with tabs for each type
- **Exam Paper Creation**: Generates formatted exams from stored questions

---

## Installation

### Prerequisites
Ensure you have the following installed:
- Python 3.8+
- Pip (Python package manager)
- Ollama for running the AI model locally
- Required Python libraries (install using the steps below)

# Install dependencies
pip install -r requirements.txt
```

### Install Ollama (if not installed)
Follow the installation guide at [Ollama's official site](https://ollama.ai/) and ensure the model `qwen2.5:1.5b` is available.

---

## Usage

### 1. Start the Application
Run the following command:
```sh
python enhanced-gradio-interface.py
```
This will launch a **Gradio interface** in your web browser.

### 2. Upload a PDF
- Go to the **Upload Documents** tab.
- Upload a PDF file and process it.
- The document’s text will be extracted and stored in a **vector database**.

### 3. Generate Questions
- Select a PDF from the dropdown.
- Choose the **difficulty level** and **question type** (MCQ, True/False, etc.).
- Click **Generate Questions** to create questions using AI.
- Questions will be displayed in an **accordion format**.
- Click **Save Questions** to store them.

### 4. View Saved Questions
- Go to the **View Question Bank** tab.
- Select a PDF and click **View Question Bank**.
- Questions are displayed in a **tabbed interface**.

### 5. Create an Exam
- Navigate to the **Create Exam** tab.
- Select a PDF and difficulty level.
- Choose the number of each question type.
- Click **Create Exam** to generate a formatted paper.

---

## Project Structure
```
project-root/
│── enhanced-gradio-interface.py   # Main Gradio UI file
│── app.py                         # Backend logic (AI & vector storage)
│── requirements.txt               # Python dependencies
│── uploads/                       # Directory for uploaded PDFs
│── vectordb/                      # Vector database storage
│── question_banks/                # Stored JSON files of questions
│── README.md                      # This documentation
```

---

## Technology Stack
- **Python** (Backend logic)
- **Gradio** (User interface)
- **LangChain** (AI-powered document processing)
- **Ollama** (AI model for generating questions)
- **Chroma** (Vector database for document retrieval)
- **PyPDF2** (PDF text extraction)

---

## Troubleshooting
### 1. Gradio UI Not Loading
Try restarting the application and checking for errors:
```sh
python enhanced-gradio-interface.py
```
Ensure Gradio is installed:
```sh
pip install gradio
```

### 2. No Questions Generated
- Make sure the PDF contains **text data** (scanned images will not work).
- Ensure **Ollama is running** and the correct model (`qwen2.5:1.5b`) is installed.

### 3. Issues with Vector Storage
If encountering errors related to Chroma, delete the `vectordb/` directory and restart the app:
```sh
rm -rf vectordb/
```

---

## License
This project is licensed under the MIT License.

