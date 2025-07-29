# Book Study Backend

An AI-powered book study system that processes PDFs, generates notes, creates quizzes, and organizes study materials.

## Features

- PDF processing and chapter extraction
- Vector database for semantic search
- AI-generated chapter notes
- Quiz generation with difficulty levels
- Question answering system
- Multi-source note organization (AI, user uploads, past tests)
- Smart study plan generation

## Quick Start

### 1. Setup

```bash
# Make setup script executable
chmod +x scripts/setup.sh

# Run setup
./scripts/setup.sh
```

### 2. Configure

Edit `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY=your-actual-api-key-here
```

### 3. Run

```bash
# Make start script executable
chmod +x scripts/start.sh

# Start the service
./scripts/start.sh
```

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## Deployment Options

### Docker

```bash
docker-compose up -d
```

### Systemd (Linux)

```bash
sudo cp systemd/book-study.service /etc/systemd/system/
sudo systemctl enable book-study
sudo systemctl start book-study
```

## API Endpoints

- `POST /upload_book` - Upload and process a PDF book
- `POST /upload_notes/{book_id}` - Upload user notes
- `POST /upload_past_test/{book_id}` - Upload and analyze past tests
- `POST /generate_quiz/{book_id}/{chapter}` - Generate chapter quiz
- `POST /ask_question/{book_id}` - Ask questions about the book
- `GET /get_notes/{book_id}` - Get organized notes by topic
- `POST /smart_study_plan/{book_id}` - Create personalized study plan

## Requirements

- Python 3.8+
- OpenAI API key
- 2GB+ RAM recommended

## License

MIT
# navi
