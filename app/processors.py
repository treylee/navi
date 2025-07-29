import re
import hashlib
from typing import List, Tuple
from pypdf import PdfReader
from app.models import Chapter

class BookProcessor:
    """Handles PDF processing and chapter extraction"""
    
    @staticmethod
    def extract_chapters(pdf_path: str) -> Tuple[str, List[Chapter]]:
        """Extract chapters from PDF"""
        reader = PdfReader(pdf_path)
        book_id = hashlib.md5(pdf_path.encode()).hexdigest()
        
        chapters = []
        chapter_pattern = re.compile(r'chapter\s+(\d+)', re.IGNORECASE)
        
        current_chapter = None
        current_content = []
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            
            # Check for chapter heading
            chapter_match = chapter_pattern.search(text)
            if chapter_match:
                # Save previous chapter
                if current_chapter:
                    current_chapter.content = '\n'.join(current_content)
                    current_chapter.page_end = page_num - 1
                    chapters.append(current_chapter)
                
                # Start new chapter
                chapter_num = int(chapter_match.group(1))
                lines = text.split('\n')
                title_idx = next((i for i, line in enumerate(lines) if chapter_match.group(0) in line.lower()), 0)
                title = lines[title_idx + 1].strip() if title_idx + 1 < len(lines) else f"Chapter {chapter_num}"
                
                current_chapter = Chapter(
                    book_id=book_id,
                    chapter_number=chapter_num,
                    title=title,
                    content="",
                    page_start=page_num,
                    page_end=page_num
                )
                current_content = [text]
            elif current_chapter:
                current_content.append(text)
        
        # Save last chapter
        if current_chapter:
            current_chapter.content = '\n'.join(current_content)
            current_chapter.page_end = len(reader.pages) - 1
            chapters.append(current_chapter)
        
        # If no chapters found, treat entire book as one chapter
        if not chapters:
            full_text = '\n'.join([page.extract_text() for page in reader.pages])
            chapters.append(Chapter(
                book_id=book_id,
                chapter_number=1,
                title="Full Book",
                content=full_text,
                page_start=0,
                page_end=len(reader.pages) - 1
            ))
        
        return book_id, chapters