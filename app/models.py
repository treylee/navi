from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional

@dataclass
class Chapter:
    book_id: str
    chapter_number: int
    title: str
    content: str
    page_start: int
    page_end: int
    
@dataclass
class Note:
    id: str
    book_id: str
    chapter_number: Optional[int]
    content: str
    source: str  # 'ai_generated', 'user_upload', 'past_test'
    topic_tags: List[str]
    created_at: datetime
    
@dataclass
class QuizQuestion:
    id: str
    book_id: str
    chapter_number: int
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty: str  # 'easy', 'medium', 'hard'
    topic: str
