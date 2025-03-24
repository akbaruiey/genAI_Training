import json
import random
import ollama
import os
from datetime import datetime
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama

class AIQuestionBankGenerator:
    def __init__(self, model="qwen2.5:1.5b", embedding_model="qwen2.5:1.5b"):
        self.model = model
        self.embedding_model = embedding_model
        
        # Initialize empty question bank
        self.question_bank = {}
        
        # Try to load existing question bank if it exists
        try:
            if os.path.exists("question_bank.json") and os.path.getsize("question_bank.json") > 0:
                with open("question_bank.json", "r") as f:
                    self.question_bank = json.load(f)
        except Exception as e:
            print(f"Error loading existing question bank: {e}")
            # Continue with empty question bank
        
        self.templates = {
            "mcq": "Generate {num} multiple choice questions about {topic} for {difficulty} level. Each question should have 4 options and one correct answer. Use the provided context information when applicable.",
            "true_false": "Generate {num} true/false questions about {topic} for {difficulty} level, including correct answers. Use the provided context information when applicable.",
            "short": "Generate {num} short answer questions about {topic} for {difficulty} level, with brief model answers. Use the provided context information when applicable.",
            "long": "Generate {num} long answer questions about {topic} for {difficulty} level, including key points. Use the provided context information when applicable."
        }
        
        # Create upload directory if it doesn't exist
        self.upload_dir = "uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Create directory for vector DB persistence
        self.vector_db_dir = "vectordb"
        os.makedirs(self.vector_db_dir, exist_ok=True)
        
        # Dictionary to store vector stores for each PDF
        self.vector_stores = {}
        self.embeddings = OllamaEmbeddings(model=self.embedding_model)
        
        # Load existing vector stores if they exist
        self._load_existing_vector_stores()
    
    def _load_existing_vector_stores(self):
        """Load existing vector stores from vectordb directory"""
        if not os.path.exists(self.vector_db_dir):
            return
            
        # Check for PDF-specific subdirectories
        for pdf_dir in os.listdir(self.vector_db_dir):
            pdf_vector_dir = os.path.join(self.vector_db_dir, pdf_dir)
            if os.path.isdir(pdf_vector_dir):
                try:
                    # Try to load the vector store for this PDF
                    vector_store = Chroma(
                        persist_directory=pdf_vector_dir,
                        embedding_function=self.embeddings
                    )
                    self.vector_stores[pdf_dir] = vector_store
                    print(f"Loaded vector store for: {pdf_dir}")
                except Exception as e:
                    print(f"Error loading vector store for {pdf_dir}: {e}")

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def process_document(self, file_path):
        """Process a document and add it to a document-specific vector store"""
        # Extract text from PDF
        document_text = self.extract_text_from_pdf(file_path)
        
        if not document_text:
            return False
        
        # Get PDF filename without path
        pdf_filename = os.path.basename(file_path)
        
        # Create a PDF-specific directory for vector store
        pdf_vector_dir = os.path.join(self.vector_db_dir, pdf_filename)
        os.makedirs(pdf_vector_dir, exist_ok=True)
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(document_text)
        
        # Create vector store specifically for this PDF
        vector_store = Chroma.from_texts(
            texts=chunks,
            embedding=self.embeddings,
            persist_directory=pdf_vector_dir
        )
        
        # Persist the vector store
        if hasattr(vector_store, 'persist'):
            vector_store.persist()
        
        # Add to our dictionary of vector stores
        self.vector_stores[pdf_filename] = vector_store
        
        return True

    def save_uploaded_file(self, file_upload):
        """Save an uploaded file to the uploads directory"""
        if not file_upload:
            return None
            
        filename = os.path.join(self.upload_dir, file_upload.name)
        with open(filename, "wb") as f:
            f.write(file_upload.read())
        return filename

    def generate_questions_with_rag(self, pdf_filename, topic, difficulty, q_type, num):
        """Generate questions using RAG for a specific PDF"""
        if q_type not in self.templates:
            raise ValueError(f"Unsupported question type: {q_type}")
            
        # Build the prompt
        prompt = self.templates[q_type].format(topic=topic, difficulty=difficulty, num=num)
        
        # If we have a vector store for this PDF, use it for RAG
        if pdf_filename in self.vector_stores:
            try:
                # Get the vector store for this specific PDF
                vector_store = self.vector_stores[pdf_filename]
                
                # Set up retrieval QA chain
                llm = Ollama(model=self.model)
                qa_chain = RetrievalQA.from_chain_type(
                    llm=llm,
                    chain_type="stuff",
                    retriever=vector_store.as_retriever(search_kwargs={"k": 3})
                )
                
                # Construct a query combining the topic and difficulty
                query = f"I need to create {q_type} questions about {topic} at {difficulty} level."
                
                # Get relevant context from this specific PDF
                docs = vector_store.similarity_search(query, k=3)
                context = "\n".join([doc.page_content for doc in docs])
                
                # Enhanced prompt with context
                enhanced_prompt = f"""
                Context information from {pdf_filename}:
                {context}
                
                Task:
                {prompt}
                
                Format each question clearly and include answers.
                """
                
                # Generate response using the QA chain
                response = ollama.chat(model=self.model, messages=[{"role": "user", "content": enhanced_prompt}])
                return response["message"]["content"].split('\n')
            except Exception as e:
                print(f"Error using RAG for generation: {e}")
                # Fall back to standard generation if RAG fails
                pass
        
        # Standard generation without RAG
        try:
            response = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt}])
            return response["message"]["content"].split('\n')
        except Exception as e:
            print("Error generating questions:", e)
            return []

    def generate_questions(self, pdf_filename, topic, difficulty, q_type, num):
        """Generate questions with RAG for a specific PDF"""
        return self.generate_questions_with_rag(pdf_filename, topic, difficulty, q_type, num)

    def add_to_bank(self, topic, difficulty, q_type, questions):
        self.question_bank.setdefault(topic, {}).setdefault(difficulty, {}).setdefault(q_type, []).extend(questions)
        print(f"Added {len(questions)} {q_type} questions to bank.")

    def save_question_bank(self, filename="question_bank.json"):
        with open(filename, "w") as f:
            json.dump(self.question_bank, f, indent=2)
        print(f"Question bank saved to {filename}")

    def generate_exam_paper(self, topic, difficulty, num_mcq=5, num_tf=3, num_short=2, num_long=1):
        exam_paper = {"title": f"{topic} Exam ({difficulty} Level)", "date": datetime.now().strftime("%Y-%m-%d"), "sections": []}
        
        for q_type, num in {"mcq": num_mcq, "true_false": num_tf, "short": num_short, "long": num_long}.items():
            if topic in self.question_bank and difficulty in self.question_bank[topic] and q_type in self.question_bank[topic][difficulty]:
                questions = random.sample(self.question_bank[topic][difficulty][q_type], min(num, len(self.question_bank[topic][difficulty][q_type])))
                exam_paper["sections"].append({"type": q_type, "questions": questions})
        
        return exam_paper
