import os
import logging
from datetime import datetime
from typing import Optional
from dataclasses import asdict

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import openai

from app.config import settings
from app.models import Chapter
from app.processors import BookProcessor
from app.vector_store import VectorStore
from app.ai_assistant import AIAssistant
from app.note_organizer import NoteOrganizer
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Book Study Assistant API",
    description="AI-powered book study system with note organization and quiz generation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
vector_store = VectorStore()
note_organizer = NoteOrganizer()

# Create necessary directories
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.notes_dir, exist_ok=True)
os.makedirs(settings.chroma_persist_dir, exist_ok=True)
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("app/index.html", "r") as f:
        return f.read()
    
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/upload_book")
async def upload_book(file: UploadFile = File(...)):
    """Upload and process a book PDF"""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file
        file_path = os.path.join(settings.upload_dir, file.filename)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Processing book: {file.filename}")
        
        # Process PDF
        processor = BookProcessor()
        book_id, chapters = processor.extract_chapters(file_path)
        
        # Index in vector store
        vector_store.index_chapters(book_id, chapters)
        
        # Generate AI notes for each chapter
        for chapter in chapters:
            ai_note = await AIAssistant.generate_chapter_notes(chapter)
            note_organizer.add_note(ai_note)
        
        logger.info(f"Successfully processed book {book_id} with {len(chapters)} chapters")
        
        return {
            "book_id": book_id,
            "filename": file.filename,
            "chapters": [
                {
                    "number": ch.chapter_number,
                    "title": ch.title,
                    "pages": f"{ch.page_start}-{ch.page_end}"
                } for ch in chapters
            ]
        }
    except Exception as e:
        logger.error(f"Error processing book: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_notes/{book_id}")
async def upload_notes(
    book_id: str, 
    file: UploadFile = File(...), 
    chapter: Optional[int] = Form(None)
):
    """Upload user notes for a book"""
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Extract topics
        topics = await AIAssistant.extract_topics(text_content)
        
        note = Note(
            id=hashlib.md5(f"{book_id}_user_{file.filename}".encode()).hexdigest(),
            book_id=book_id,
            chapter_number=chapter,
            content=text_content,
            source="user_upload",
            topic_tags=topics,
            created_at=datetime.now()
        )
        
        note_organizer.add_note(note)
        
        logger.info(f"Added user notes for book {book_id}")
        
        return {"message": "Notes uploaded successfully", "note_id": note.id}
    except Exception as e:
        logger.error(f"Error uploading notes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_past_test/{book_id}")
async def upload_past_test(book_id: str, file: UploadFile = File(...)):
    """Upload past test for analysis"""
    try:
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Process test and create notes
        notes = await note_organizer.process_past_test(book_id, text_content, vector_store)
        
        for note in notes:
            note_organizer.add_note(note)
        
        logger.info(f"Processed past test for book {book_id}, created {len(notes)} notes")
        
        return {
            "message": "Past test processed successfully",
            "notes_created": len(notes)
        }
    except Exception as e:
        logger.error(f"Error processing past test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_quiz/{book_id}/{chapter_number}")
async def generate_quiz(
    book_id: str, 
    chapter_number: int, 
    difficulty: str = "medium", 
    num_questions: int = 5
):
    """Generate quiz for a chapter"""
    try:
        # In production, retrieve chapter from database
        # For now, creating a placeholder
        chapter = Chapter(
            book_id=book_id,
            chapter_number=chapter_number,
            title=f"Chapter {chapter_number}",
            content="Chapter content here...",  # Would be retrieved from DB
            page_start=0,
            page_end=10
        )
        
        questions = await AIAssistant.generate_quiz(chapter, difficulty, num_questions)
        
        logger.info(f"Generated {len(questions)} quiz questions for book {book_id}, chapter {chapter_number}")
        
        return {
            "quiz": [asdict(q) for q in questions]
        }
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask_question/{book_id}")
async def ask_question(book_id: str, question: str = Form(...)):
    """Ask a question about the book"""
    try:
        answer = await AIAssistant.answer_question(book_id, question, vector_store)
        
        logger.info(f"Answered question for book {book_id}")
        
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_notes/{book_id}")
async def get_notes(book_id: str, chapter: Optional[int] = None):
    """Get organized notes for a book or chapter"""
    try:
        organized_notes = note_organizer.merge_notes(book_id, chapter)
        
        # Convert notes to dict format
        result = {}
        for topic, notes in organized_notes.items():
            result[topic] = [
                {
                    "id": note.id,
                    "content": note.content,
                    "source": note.source,
                    "created_at": note.created_at.isoformat()
                } for note in notes
            ]
        
        return result
    except Exception as e:
        logger.error(f"Error getting notes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=(settings.app_env == "development")
    )
@app.post("/smart_study_plan/{book_id}")
async def create_study_plan(
    book_id: str, 
    exam_date: str = Form(...), 
    study_hours_per_day: int = Form(...)
):
    """Create an AI-powered study plan"""
    try:
        prompt = f"""
        Create a study plan for a book with the following parameters:
        - Exam date: {exam_date}
        - Study hours per day: {study_hours_per_day}
        
        The plan should include:
        1. Daily chapter assignments
        2. Review sessions
        3. Quiz practice times
        4. Focus areas based on past test patterns
        
        Format as a structured daily plan.
        """
        
        # Updated API call
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert study planner."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        logger.info(f"Created study plan for book {book_id}")
        
        return {"study_plan": response.choices[0].message.content}
    except Exception as e:
        logger.error(f"Error creating study plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
