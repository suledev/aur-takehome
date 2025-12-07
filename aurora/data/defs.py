import os

DB_FILE = os.getenv("DB_FILE", "aurora.db")
DATABASE_URL = f"sqlite:///{DB_FILE}"

FETCH_LIMIT = 500
SOURCE_URL = "https://november7-730026606190.europe-west1.run.app/messages"