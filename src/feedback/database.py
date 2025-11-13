"""
Database schema and initialization for feedback storage.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime

class FeedbackDatabase:
    """SQLite database for storing user feedback"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize feedback database.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "feedback.db"
        else:
            db_path = Path(db_path)
        
        # Create data directory if needed
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = str(db_path)
        self._init_database()
    
    def _init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Input
                log_file TEXT,
                log_content TEXT NOT NULL,
                platform TEXT,
                
                -- ML Prediction
                ml_predicted_category TEXT NOT NULL,
                ml_confidence REAL NOT NULL,
                ml_probabilities TEXT,
                
                -- LLM Response (if hybrid mode)
                llm_explanation TEXT,
                llm_tokens INTEGER,
                analysis_mode TEXT NOT NULL,  -- ml-only, hybrid, llm-only
                
                -- User Feedback
                user_rating INTEGER,  -- 1 (bad) to 5 (excellent)
                is_correct BOOLEAN,
                correct_category TEXT,
                user_comments TEXT,
                
                -- Metadata
                model_version TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Training data export log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_exports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                export_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                num_samples INTEGER,
                export_path TEXT,
                notes TEXT
            )
        """)
        
        # Model retraining history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retraining_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                retrain_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                num_training_samples INTEGER,
                num_feedback_samples INTEGER,
                old_accuracy REAL,
                new_accuracy REAL,
                model_path TEXT,
                notes TEXT
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_category 
            ON feedback(ml_predicted_category)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_correct 
            ON feedback(is_correct)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_timestamp 
            ON feedback(timestamp)
        """)
        
        conn.commit()
        conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn
    
    def execute(self, query: str, params: tuple = ()):
        """Execute a query and return results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        results = cursor.fetchall()
        conn.close()
        return results
    
    def execute_one(self, query: str, params: tuple = ()):
        """Execute a query and return single result"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        result = cursor.fetchone()
        conn.close()
        return result
