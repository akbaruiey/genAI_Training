import gradio as gr
import json
import os
from app import AIQuestionBankGenerator

# Initialize generator
generator = AIQuestionBankGenerator()

# Helper functions to format the display
def format_question(question, q_type):
    if not question or question.strip() == "":
        return ""
    
    formatted = question.strip()
    
    # Add some styling based on question type
    if q_type == "mcq":
        # Format MCQ questions
        formatted = formatted.replace("**Question**:", "<b>Question:</b>")
        formatted = formatted.replace("**Option A**:", "<b>A:</b>")
        formatted = formatted.replace("**Option B**:", "<b>B:</b>")
        formatted = formatted.replace("**Option C**:", "<b>C:</b>")
        formatted = formatted.replace("**Option D**:", "<b>D:</b>")
        formatted = formatted.replace("**Answer**:", "<b>Answer:</b>")
    elif q_type == "true_false":
        # Format true/false questions
        if "- True" in formatted:
            formatted = formatted.replace("- True", "<b>Answer: True</b>")
        elif "- False" in formatted:
            formatted = formatted.replace("- False", "<b>Answer: False</b>")
    elif q_type == "short" or q_type == "long":
        # Format short/long answer questions
        formatted = formatted.replace("**Question:**", "<b>Question:</b>")
        formatted = formatted.replace("**Short Answer Answer:**", "<b>Answer:</b>")
        formatted = formatted.replace("**Answer:**", "<b>Answer:</b>")
        
    return formatted.replace("\n", "<br>")

def get_pdf_specific_question_bank(pdf_filename):
    """Get the PDF-specific question bank if it exists"""
    # Create filename for the PDF-specific question bank
    bank_filename = os.path.splitext(pdf_filename)[0] + "_questions.json"
    bank_path = os.path.join("question_banks", bank_filename)
    
    if os.path.exists(bank_path):
        try:
            with open(bank_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading PDF-specific question bank: {e}")
    
    # If file doesn't exist or has an error, return empty dict
    return {}

def save_pdf_specific_question_bank(pdf_filename, question_bank):
    """Save a PDF-specific question bank"""
    # Create directory if it doesn't exist
    os.makedirs("question_banks", exist_ok=True)
    
    # Create filename for the PDF-specific question bank
    bank_filename = os.path.splitext(pdf_filename)[0] + "_questions.json"
    bank_path = os.path.join("question_banks", bank_filename)
    
    try:
        with open(bank_path, "w") as f:
            json.dump(question_bank, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving PDF-specific question bank: {e}")
        return False

# Function to get list of uploaded PDF files
def get_uploaded_pdfs():
    upload_dir = generator.upload_dir
    if not os.path.exists(upload_dir):
        return []
    
    pdf_files = [f for f in os.listdir(upload_dir) if f.lower().endswith('.pdf')]
    return pdf_files

# Function to handle document upload
def upload_document(file):
    if file is None:
        return "No file uploaded.", get_uploaded_pdfs()
    
    try:
        # For Gradio file uploads, file might be a path or file-like object
        if isinstance(file, str):
            # If file is already a path
            file_path = file
            filename = os.path.basename(file_path)
            # Copy to uploads directory
            import shutil
            dest_path = os.path.join(generator.upload_dir, filename)
            shutil.copy(file_path, dest_path)
            file_path = dest_path
        else:
            # Try to get the file path if it's a file object
            try:
                file_path = file.name
                filename = os.path.basename(file_path)
                # Copy to uploads directory
                import shutil
                dest_path = os.path.join(generator.upload_dir, filename)
                shutil.copy(file_path, dest_path)
                file_path = dest_path
            except (AttributeError, TypeError):
                # Fall back to reading the file content
                try:
                    filename = os.path.basename(getattr(file, 'name', 'uploaded_file.pdf'))
                    file_path = os.path.join(generator.upload_dir, filename)
                    with open(file_path, "wb") as f:
                        f.write(file.read())
                except Exception as e:
                    return f"Failed to save file: {str(e)}", get_uploaded_pdfs()
        
        success = generator.process_document(file_path)
        if success:
            return f"Successfully processed and vectorized: {os.path.basename(file_path)}", get_uploaded_pdfs()
        else:
            return f"Failed to process document: {os.path.basename(file_path)}", get_uploaded_pdfs()
    except Exception as e:
        return f"Error processing document: {str(e)}", get_uploaded_pdfs()

# Extract topic from PDF filename (remove extension and replace underscores with spaces)
def extract_topic_from_filename(filename):
    return os.path.splitext(filename)[0].replace('_', ' ')

# Generate questions
def generate_questions(pdf_file, difficulty, q_type, num_questions):
    if not pdf_file:
        return "Please select a PDF first.", []
    
    # Extract topic from the PDF filename
    topic = extract_topic_from_filename(pdf_file)
    
    # Generate questions
    questions = generator.generate_questions(pdf_file, topic, difficulty, q_type, int(num_questions))
    
    return f"Generated {len(questions)} {q_type} questions", questions

# Save generated questions to PDF-specific question bank
def save_questions(pdf_file, difficulty, q_type, questions):
    if not pdf_file or not questions:
        return "No questions to save."
    
    # Extract topic from the PDF filename
    topic = extract_topic_from_filename(pdf_file)
    
    # Load existing PDF-specific question bank
    question_bank = get_pdf_specific_question_bank(pdf_file)
    
    # Add new questions
    question_bank.setdefault(topic, {}).setdefault(difficulty, {}).setdefault(q_type, []).extend(questions)
    
    # Save the updated question bank
    if save_pdf_specific_question_bank(pdf_file, question_bank):
        return f"Saved {len(questions)} {q_type} questions to {pdf_file} question bank."
    else:
        return "Failed to save questions."

# Format and display the questions
def format_questions_display(questions, q_type):
    if not questions:
        return "<p>No questions generated yet.</p>"
    
    html = "<div style='max-height: 500px; overflow-y: auto;'>"
    for i, question in enumerate(questions):
        html += f"<div id='question-{i}' style='margin-bottom:15px; padding:10px; border:1px solid #ddd; border-radius:5px;'>"
        html += format_question(question, q_type)
        html += "</div>"
    html += "</div>"
    
    return html

# Format and display the PDF-specific question bank
def format_pdf_question_bank(pdf_file):
    if not pdf_file:
        return "<p>Please select a PDF first.</p>"
    
    question_bank = get_pdf_specific_question_bank(pdf_file)
    if not question_bank:
        return f"<p>No questions saved for {pdf_file} yet.</p>"
    
    html = f"<h2>Question Bank for {pdf_file}</h2>"
    
    for topic in question_bank:
        html += f"<h3>Topic: {topic}</h3>"
        
        for difficulty in question_bank[topic]:
            html += f"<h4>Difficulty: {difficulty}</h4>"
            
            for q_type in question_bank[topic][difficulty]:
                if q_type == "mcq":
                    type_name = "Multiple Choice Questions"
                elif q_type == "true_false":
                    type_name = "True/False Questions"
                elif q_type == "short":
                    type_name = "Short Answer Questions"
                elif q_type == "long":
                    type_name = "Long Answer Questions"
                else:
                    type_name = q_type
                    
                html += f"<h5>{type_name} ({len(question_bank[topic][difficulty][q_type])} questions)</h5>"
                
                html += "<div style='max-height: 400px; overflow-y: auto;'>"
                for i, question in enumerate(question_bank[topic][difficulty][q_type]):
                    if question.strip():  # Skip empty questions
                        html += f"<div style='margin-bottom:15px; padding:10px; border:1px solid #ddd; border-radius:5px;'>"
                        html += format_question(question, q_type)
                        html += "</div>"
                html += "</div>"
    
    return html

# Define the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# AI Question Bank Generator with RAG")
    
    # State for storing PDF dropdown values and current questions
    pdf_files = gr.State(get_uploaded_pdfs())
    current_questions = gr.State([])
    current_q_type = gr.State("")
    
    with gr.Tabs():
        with gr.TabItem("Upload Documents"):
            gr.Markdown("## Upload PDF Documents for Context")
            file_upload = gr.File(label="Upload PDF", file_types=[".pdf"])
            upload_btn = gr.Button("Process Document")
            upload_status = gr.Textbox(label="Upload Status")
            
            upload_btn.click(upload_document, 
                           inputs=[file_upload],
                           outputs=[upload_status, pdf_files])
    
        with gr.TabItem("Generate Questions"):
            gr.Markdown("## Generate Questions from Context")
            with gr.Row():
                # Use PDF dropdown for selecting the specific document
                pdf_dropdown = gr.Dropdown(label="Select PDF Document", choices=get_uploaded_pdfs(), interactive=True)
                difficulty = gr.Dropdown(["beginner", "intermediate", "advanced"], label="Difficulty", value="beginner")
            
            with gr.Row():
                # Question type dropdown
                question_type = gr.Dropdown(
                    ["mcq", "true_false", "short", "long"], 
                    label="Question Type", 
                    value="mcq",
                    info="MCQs, True/False, Short Answer, or Long Answer"
                )
                num_questions = gr.Number(label="Number of Questions", value=5, minimum=1, maximum=20)
                
            generate_btn = gr.Button("Generate Questions")
            status_output = gr.Textbox(label="Status")
            
            # Display area for generated questions
            questions_display = gr.HTML(label="Generated Questions")
            
            with gr.Row():
                save_btn = gr.Button("Save Questions")
                regenerate_btn = gr.Button("Regenerate Questions")
            
            # Update dropdown choices when pdf_files state changes
            pdf_files.change(lambda x: gr.Dropdown.update(choices=x), inputs=pdf_files, outputs=pdf_dropdown)
            
            # Generate questions function
            def generate_and_display(pdf_file, difficulty, q_type, num):
                status, questions = generate_questions(pdf_file, difficulty, q_type, num)
                display_html = format_questions_display(questions, q_type)
                return status, display_html, questions, q_type
            
            generate_btn.click(
                generate_and_display, 
                inputs=[pdf_dropdown, difficulty, question_type, num_questions],
                outputs=[status_output, questions_display, current_questions, current_q_type]
            )
            
            # Regenerate with the same parameters
            def regenerate(pdf_file, difficulty, q_type, num):
                status, questions = generate_questions(pdf_file, difficulty, q_type, num)
                display_html = format_questions_display(questions, q_type)
                return status, display_html, questions, q_type
                
            regenerate_btn.click(
                regenerate,
                inputs=[pdf_dropdown, difficulty, question_type, num_questions],
                outputs=[status_output, questions_display, current_questions, current_q_type]
            )
            
            # Save questions function
            def save_current_questions(pdf_file, difficulty, q_type, questions):
                save_status = save_questions(pdf_file, difficulty, q_type, questions)
                return save_status
                
            save_btn.click(
                save_current_questions,
                inputs=[pdf_dropdown, difficulty, current_q_type, current_questions],
                outputs=[status_output]
            )
        
        with gr.TabItem("View Question Bank"):
            gr.Markdown("## View PDF-specific Question Banks")
            
            # Dropdown to select PDF for viewing its question bank
            view_pdf_dropdown = gr.Dropdown(label="Select PDF Document", choices=get_uploaded_pdfs(), interactive=True)
            view_btn = gr.Button("View Question Bank")
            
            # Display area for PDF-specific question bank
            bank_display = gr.HTML(label="Question Bank Contents")
            
            # Update dropdown choices when pdf_files state changes
            pdf_files.change(lambda x: gr.Dropdown.update(choices=x), inputs=pdf_files, outputs=view_pdf_dropdown)
            
            # View PDF-specific question bank
            view_btn.click(
                format_pdf_question_bank,
                inputs=[view_pdf_dropdown],
                outputs=[bank_display]
            )
            
        with gr.TabItem("Create Exam"):
            gr.Markdown("## Create Exam from PDF-specific Question Bank")
            
            with gr.Row():
                # Use PDF dropdown for selecting the specific document
                exam_pdf_dropdown = gr.Dropdown(label="Select PDF Document", choices=get_uploaded_pdfs(), interactive=True)
                exam_difficulty = gr.Dropdown(["beginner", "intermediate", "advanced"], label="Difficulty", value="beginner")
            
            with gr.Row():
                exam_mcq = gr.Number(label="MCQs", value=5, minimum=0)
                exam_tf = gr.Number(label="True/False", value=3, minimum=0)
                exam_short = gr.Number(label="Short Answer", value=2, minimum=0)
                exam_long = gr.Number(label="Long Answer", value=1, minimum=0)
                
            # Function to create an exam from PDF-specific question bank
            def create_exam_from_pdf_bank(pdf_file, difficulty, mcq, tf, short, long):
                if not pdf_file:
                    return "Please select a PDF first.", ""
                
                # Extract topic from the PDF filename
                topic = extract_topic_from_filename(pdf_file)
                
                # Load PDF-specific question bank
                question_bank = get_pdf_specific_question_bank(pdf_file)
                
                # Check if there are questions for this topic and difficulty
                if topic not in question_bank or difficulty not in question_bank[topic]:
                    return f"No questions found for {topic} at {difficulty} level.", ""
                
                # Create exam structure
                exam = {
                    "title": f"{topic} Exam ({difficulty} Level)",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "sections": []
                }
                
                # Add questions to exam
                for q_type, num in {"mcq": mcq, "true_false": tf, "short": short, "long": long}.items():
                    if q_type in question_bank[topic][difficulty] and num > 0:
                        available_questions = question_bank[topic][difficulty][q_type]
                        selected_questions = random.sample(available_questions, min(int(num), len(available_questions)))
                        exam["sections"].append({"type": q_type, "questions": selected_questions})
                
                # Format exam for display
                formatted_exam = format_exam_paper(exam)
                
                return json.dumps(exam, indent=2), formatted_exam
                
            exam_btn = gr.Button("Create Exam")
            exam_json = gr.Textbox(label="Raw JSON")
            formatted_exam = gr.HTML(label="Formatted Exam")
            
            # Update dropdown choices when pdf_files state changes
            pdf_files.change(lambda x: gr.Dropdown.update(choices=x), inputs=pdf_files, outputs=exam_pdf_dropdown)
            
            # Format exam paper for display
            def format_exam_paper(exam_data):
                try:
                    if isinstance(exam_data, str):
                        exam = json.loads(exam_data)
                    else:
                        exam = exam_data
                        
                    html = f"<h2>{exam['title']}</h2>"
                    html += f"<p>Date: {exam['date']}</p><hr>"
                    
                    for section_idx, section in enumerate(exam['sections']):
                        q_type = section['type']
                        html += f"<h3>Section {section_idx + 1}: "
                        
                        if q_type == "mcq":
                            html += "Multiple Choice Questions</h3>"
                        elif q_type == "true_false":
                            html += "True/False Questions</h3>"
                        elif q_type == "short":
                            html += "Short Answer Questions</h3>"
                        elif q_type == "long":
                            html += "Long Answer Questions</h3>"
                        
                        for i, question in enumerate(section['questions']):
                            html += f"<div style='margin-bottom:15px; padding:10px; border:1px solid #ddd; border-radius:5px;'>"
                            html += format_question(question, q_type)
                            html += "</div>"
                            
                    return html
                except Exception as e:
                    return f"<p>Error formatting exam: {str(e)}</p><pre>{exam_data}</pre>"
            
            exam_btn.click(
                create_exam_from_pdf_bank,
                inputs=[exam_pdf_dropdown, exam_difficulty, exam_mcq, exam_tf, exam_short, exam_long],
                outputs=[exam_json, formatted_exam]
            )

# Import missing dependencies
from datetime import datetime
import random

# Launch the app
demo.launch()