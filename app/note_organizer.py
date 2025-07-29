import re
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from app.models import Note
from app.ai_assistant import AIAssistant
from app.vector_store import VectorStore

class NoteOrganizer:
    """Manages and organizes notes from various sources"""
    
    def __init__(self):
        self.notes_db = {}  # In production, use a proper database
    
    def add_note(self, note: Note):
        """Add a note to the system"""
        if note.book_id not in self.notes_db:
            self.notes_db[note.book_id] = []
        self.notes_db[note.book_id].append(note)
    
    def merge_notes(self, book_id: str, chapter_number: Optional[int] = None) -> Dict[str, List[Note]]:
        """Merge and organize notes by topic"""
        if book_id not in self.notes_db:
            return {}
        
        notes = self.notes_db[book_id]
        if chapter_number:
            notes = [n for n in notes if n.chapter_number == chapter_number]
        
        # Group by topics
        topic_notes = {}
        for note in notes:
            for topic in note.topic_tags:
                if topic not in topic_notes:
                    topic_notes[topic] = []
                topic_notes[topic].append(note)
        
        return topic_notes
    
    async def process_past_test(self, book_id: str, test_content: str, vector_store: VectorStore) -> List[Note]:
        """Process past test and create relevant notes"""
        # Extract questions from test
        questions = re.findall(r'\d+\.\s*(.+?\?)', test_content, re.DOTALL)
        
        notes = []
        for question in questions:
            # Find relevant chapter
            search_results = vector_store.search(book_id, question, n_results=1)
            if search_results['metadatas'][0]:
                chapter_num = search_results['metadatas'][0][0].get('chapter_number', None)
            else:
                chapter_num = None
            
            # Generate note based on question
            note_content = f"Past Test Question: {question}\n\n"
            
            # Get AI explanation
            explanation = await AIAssistant.answer_question(book_id, question, vector_store)
            note_content += f"Key Concept: {explanation}"
            
            # Extract topics
            topics = await AIAssistant.extract_topics(note_content)
            
            note = Note(
                id=hashlib.md5(f"{book_id}_test_{question[:20]}".encode()).hexdigest(),
                book_id=book_id,
                chapter_number=chapter_num,
                content=note_content,
                source="past_test",
                topic_tags=topics,
                created_at=datetime.now()
            )
            notes.append(note)
        
        return notes
