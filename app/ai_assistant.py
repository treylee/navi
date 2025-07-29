import json
import hashlib
from datetime import datetime
from typing import List
from openai import OpenAI
from app.models import Chapter, Note, QuizQuestion
from app.vector_store import VectorStore
from app.config import settings

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)

class AIAssistant:
    """Handles AI-powered features"""
    
    @staticmethod
    async def generate_chapter_notes(chapter: Chapter) -> Note:
        """Generate AI notes for a chapter"""
        prompt = f"""
        Create comprehensive study notes for the following chapter:
        
        Chapter {chapter.chapter_number}: {chapter.title}
        
        Content: {chapter.content[:3000]}...
        
        Please create notes that include:
        1. Key concepts and definitions
        2. Important formulas or processes
        3. Main arguments or themes
        4. Critical examples
        5. Summary of main points
        
        Format the notes in a clear, structured manner suitable for studying.
        """
        
        # Updated API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert study assistant creating comprehensive notes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        note_content = response.choices[0].message.content
        
        # Extract topics using AI
        topics = await AIAssistant.extract_topics(note_content)
        
        return Note(
            id=hashlib.md5(f"{chapter.book_id}_{chapter.chapter_number}_ai".encode()).hexdigest(),
            book_id=chapter.book_id,
            chapter_number=chapter.chapter_number,
            content=note_content,
            source="ai_generated",
            topic_tags=topics,
            created_at=datetime.now()
        )
    
    @staticmethod
    async def extract_topics(text: str) -> List[str]:
        """Extract topic tags from text"""
        prompt = f"""
        Extract 3-5 main topic tags from the following text. 
        Return only the topics as a comma-separated list.
        
        Text: {text[:1000]}...
        """
        
        # Updated API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Extract main topics from text. Return only comma-separated topics."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        topics = response.choices[0].message.content.strip().split(',')
        return [topic.strip() for topic in topics]
    
    @staticmethod
    async def generate_quiz(chapter: Chapter, difficulty: str = "medium", num_questions: int = 5) -> List[QuizQuestion]:
        """Generate quiz questions for a chapter"""
        prompt = f"""
        Create {num_questions} {difficulty} multiple-choice questions based on this chapter:
        
        Chapter {chapter.chapter_number}: {chapter.title}
        Content: {chapter.content[:4000]}...
        
        For each question, provide:
        1. The question
        2. 4 answer options (A, B, C, D)
        3. The correct answer (A, B, C, or D)
        4. A brief explanation
        5. The main topic being tested
        
        Format as JSON array with structure:
        [{{
            "question": "...",
            "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
            "correct_answer": "A",
            "explanation": "...",
            "topic": "..."
        }}]
        """
        
        # Updated API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert quiz creator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        
        quiz_data = json.loads(response.choices[0].message.content)
        
        questions = []
        for i, q in enumerate(quiz_data):
            questions.append(QuizQuestion(
                id=hashlib.md5(f"{chapter.book_id}_{chapter.chapter_number}_q{i}".encode()).hexdigest(),
                book_id=chapter.book_id,
                chapter_number=chapter.chapter_number,
                question=q["question"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                difficulty=difficulty,
                topic=q["topic"]
            ))
        
        return questions
    
    @staticmethod
    async def answer_question(book_id: str, question: str, vector_store: VectorStore) -> str:
        """Answer questions about the book"""
        # Search for relevant content
        search_results = vector_store.search(book_id, question, n_results=5)
        
        if not search_results['documents'][0]:
            return "I couldn't find relevant information to answer your question."
        
        # Prepare context from search results
        context = "\n\n".join(search_results['documents'][0])
        
        prompt = f"""
        Based on the following context from the book, answer the question:
        
        Context:
        {context}
        
        Question: {question}
        
        Provide a comprehensive answer based only on the given context.
        """
        
        # Updated API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful study assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        
        return response.choices[0].message.content