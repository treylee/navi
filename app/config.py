import os

load_dotenv()

class Settings:
    # OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
 
    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_workers: int = 4
    
    # Paths
    chroma_persist_dir: str = "./data/chroma_db"
    upload_dir: str = "./data/uploads"
    notes_dir: str = "./data/notes"
    log_file: str = "./logs/app.log"
    
    # Security
    secret_key: str = "default-secret-key"
    allowed_origins: list = ["*"]
    
    # Model Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Logging
    log_level: str = "INFO"

settings = Settings()