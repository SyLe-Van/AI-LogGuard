"""
Feedback Manager - Handle user feedback collection and analysis
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

from .database import FeedbackDatabase


class FeedbackManager:
    """Manages user feedback collection and analysis"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize FeedbackManager.
        
        Args:
            db_path: Optional custom database path
        """
        self.db = FeedbackDatabase(db_path)
    
    def save_feedback(
        self,
        log_content: str,
        ml_prediction: Dict[str, Any],
        analysis_mode: str,
        user_rating: Optional[int] = None,
        is_correct: Optional[bool] = None,
        correct_category: Optional[str] = None,
        user_comments: Optional[str] = None,
        log_file: Optional[str] = None,
        platform: Optional[str] = None,
        llm_explanation: Optional[str] = None,
        llm_tokens: Optional[int] = None,
        model_version: Optional[str] = None,
    ) -> int:
        """
        Save user feedback to database.
        
        Args:
            log_content: Full log text
            ml_prediction: Dict with error_type, confidence, probabilities
            analysis_mode: ml-only, hybrid, or llm-only
            user_rating: 1-5 rating (optional)
            is_correct: Whether ML prediction was correct (optional)
            correct_category: Correct category if prediction was wrong (optional)
            user_comments: Additional user comments (optional)
            log_file: Source log file path (optional)
            platform: CI/CD platform (optional)
            llm_explanation: LLM response text (optional)
            llm_tokens: Number of tokens used (optional)
            model_version: Model version identifier (optional)
        
        Returns:
            Feedback ID
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Serialize probabilities
        probabilities_json = json.dumps(ml_prediction.get('probabilities', {}))
        
        cursor.execute("""
            INSERT INTO feedback (
                log_file, log_content, platform,
                ml_predicted_category, ml_confidence, ml_probabilities,
                llm_explanation, llm_tokens, analysis_mode,
                user_rating, is_correct, correct_category, user_comments,
                model_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_file,
            log_content,
            platform,
            ml_prediction['error_type'],
            ml_prediction['confidence'],
            probabilities_json,
            llm_explanation,
            llm_tokens,
            analysis_mode,
            user_rating,
            is_correct,
            correct_category,
            user_comments,
            model_version or "v1.0"
        ))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return feedback_id
    
    def get_feedback_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get feedback statistics for the last N days.
        
        Args:
            days: Number of days to include
        
        Returns:
            Dictionary with statistics
        """
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Total feedback count
        cursor.execute("""
            SELECT COUNT(*) FROM feedback 
            WHERE timestamp >= ?
        """, (since_date,))
        total_feedback = cursor.fetchone()[0]
        
        # Average rating
        cursor.execute("""
            SELECT AVG(user_rating) FROM feedback 
            WHERE timestamp >= ? AND user_rating IS NOT NULL
        """, (since_date,))
        avg_rating = cursor.fetchone()[0] or 0
        
        # Accuracy (% correct predictions)
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                COUNT(*) as total
            FROM feedback 
            WHERE timestamp >= ? AND is_correct IS NOT NULL
        """, (since_date,))
        row = cursor.fetchone()
        accuracy = (row[0] / row[1] * 100) if row[1] > 0 else 0
        
        # Category distribution
        cursor.execute("""
            SELECT ml_predicted_category, COUNT(*) as count
            FROM feedback 
            WHERE timestamp >= ?
            GROUP BY ml_predicted_category
            ORDER BY count DESC
        """, (since_date,))
        category_dist = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Mode usage
        cursor.execute("""
            SELECT analysis_mode, COUNT(*) as count
            FROM feedback 
            WHERE timestamp >= ?
            GROUP BY analysis_mode
        """, (since_date,))
        mode_usage = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Corrections needed (wrong predictions)
        cursor.execute("""
            SELECT COUNT(*) FROM feedback 
            WHERE timestamp >= ? AND is_correct = 0
        """, (since_date,))
        corrections_needed = cursor.fetchone()[0]
        
        # Average confidence
        cursor.execute("""
            SELECT AVG(ml_confidence) FROM feedback 
            WHERE timestamp >= ?
        """, (since_date,))
        avg_confidence = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_feedback': total_feedback,
            'avg_rating': round(avg_rating, 2),
            'accuracy': round(accuracy, 2),
            'corrections_needed': corrections_needed,
            'avg_confidence': round(avg_confidence * 100, 2),
            'category_distribution': category_dist,
            'mode_usage': mode_usage,
            'period_days': days
        }
    
    def get_training_data(
        self,
        include_incorrect_only: bool = False,
        min_confidence: float = 0.0,
        max_confidence: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Export feedback data for model retraining.
        
        Args:
            include_incorrect_only: Only include user-corrected samples
            min_confidence: Minimum ML confidence threshold
            max_confidence: Maximum ML confidence threshold
        
        Returns:
            List of training samples
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                log_content,
                ml_predicted_category,
                ml_confidence,
                correct_category,
                is_correct,
                platform
            FROM feedback
            WHERE ml_confidence >= ? AND ml_confidence <= ?
        """
        params = [min_confidence, max_confidence]
        
        if include_incorrect_only:
            query += " AND is_correct = 0 AND correct_category IS NOT NULL"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        training_data = []
        for row in rows:
            # Use correct_category if available, otherwise use ML prediction
            label = row['correct_category'] if row['correct_category'] else row['ml_predicted_category']
            
            training_data.append({
                'log_content': row['log_content'],
                'label': label,
                'original_prediction': row['ml_predicted_category'],
                'confidence': row['ml_confidence'],
                'platform': row['platform'],
                'is_corrected': row['is_correct'] == 0
            })
        
        conn.close()
        return training_data
    
    def export_training_data(
        self,
        output_path: str,
        include_incorrect_only: bool = False
    ) -> int:
        """
        Export feedback data to JSON file for retraining.
        
        Args:
            output_path: Path to save JSON file
            include_incorrect_only: Only export corrected samples
        
        Returns:
            Number of samples exported
        """
        data = self.get_training_data(include_incorrect_only=include_incorrect_only)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Log export
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO training_exports (num_samples, export_path, notes)
            VALUES (?, ?, ?)
        """, (
            len(data),
            output_path,
            "Incorrect only" if include_incorrect_only else "All feedback"
        ))
        conn.commit()
        conn.close()
        
        return len(data)
    
    def log_retraining(
        self,
        num_training_samples: int,
        num_feedback_samples: int,
        old_accuracy: float,
        new_accuracy: float,
        model_path: str,
        notes: Optional[str] = None
    ):
        """
        Log model retraining event.
        
        Args:
            num_training_samples: Total training samples used
            num_feedback_samples: Number of feedback samples included
            old_accuracy: Accuracy before retraining
            new_accuracy: Accuracy after retraining
            model_path: Path where new model was saved
            notes: Optional notes
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO retraining_history (
                num_training_samples, num_feedback_samples,
                old_accuracy, new_accuracy, model_path, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            num_training_samples,
            num_feedback_samples,
            old_accuracy,
            new_accuracy,
            model_path,
            notes
        ))
        
        conn.commit()
        conn.close()
    
    def get_retraining_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get model retraining history.
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of retraining events
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                retrain_timestamp,
                num_training_samples,
                num_feedback_samples,
                old_accuracy,
                new_accuracy,
                model_path,
                notes
            FROM retraining_history
            ORDER BY retrain_timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_low_confidence_samples(
        self,
        threshold: float = 0.7,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get samples where ML had low confidence (needs review).
        
        Args:
            threshold: Confidence threshold (samples below this)
            limit: Maximum number of samples
        
        Returns:
            List of low-confidence samples
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id,
                log_file,
                ml_predicted_category,
                ml_confidence,
                is_correct,
                correct_category,
                timestamp
            FROM feedback
            WHERE ml_confidence < ? AND is_correct IS NULL
            ORDER BY ml_confidence ASC
            LIMIT ?
        """, (threshold, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
