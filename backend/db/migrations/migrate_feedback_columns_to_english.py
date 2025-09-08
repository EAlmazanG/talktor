#!/usr/bin/env python3
"""
Migration script to rename feedback table columns from Spanish to English
"""

import sys
import os
from pathlib import Path

def _find_repo_root(start: Path) -> Path:
    """Walk up from start until a directory containing 'backend' is found."""
    p = start.resolve()
    while p != p.parent:
        if (p / "backend").exists():
            return p
        p = p.parent
    return start.resolve()

# Ensure backend is on sys.path regardless of where the script is executed from
repo_root = _find_repo_root(Path(__file__).parent)
backend_path = repo_root / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from db.database import engine
from core.logging import setup_logging
import logging

# Setup logging
setup_logging(service_name="migrate_feedback_columns_to_english")
logger = logging.getLogger(__name__)

def migrate_feedback_columns():
    """Migrate feedback table columns from Spanish to English names"""
    
    logger.info("🚀 Starting feedback columns migration to English...")
    
    # Column mappings: old_name -> new_name
    column_mappings = {
        'feedback_general': 'general_feedback',
        'errores_generales': 'general_errors', 
        'sugerencias_generales': 'general_suggestions',
        'pronunciation_resumen': 'pronunciation_summary',
        'pronunciation_errores': 'pronunciation_errors',
        'pronunciation_sugerencias': 'pronunciation_suggestions',
        'fluency_resumen': 'fluency_summary',
        'fluency_errores': 'fluency_errors',
        'fluency_sugerencias': 'fluency_suggestions',
        'grammar_resumen': 'grammar_summary',
        'grammar_errores': 'grammar_errors',
        'grammar_sugerencias': 'grammar_suggestions',
        'expressions_resumen': 'expressions_summary',
        'expressions_errores': 'expressions_errors',
        'expressions_sugerencias': 'expressions_suggestions',
        'vocabulary_resumen': 'vocabulary_summary',
        'vocabulary_errores': 'vocabulary_errors',
        'vocabulary_sugerencias': 'vocabulary_suggestions',
        'comprehension_resumen': 'comprehension_summary',
        'comprehension_errores': 'comprehension_errors',
        'comprehension_sugerencias': 'comprehension_suggestions'
    }
    
    try:
        with engine.connect() as connection:
            # Check if feedback table exists
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'feedback'
                );
            """))
            
            table_exists = result.scalar()
            
            if not table_exists:
                logger.warning("⚠️ Feedback table does not exist. Creating new table with English columns...")
                # Import and create tables with new schema
                from db.models import Base
                Base.metadata.create_all(bind=engine)
                logger.info("✅ Created new feedback table with English column names")
                return
            
            # Check which columns exist
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'feedback'
            """))
            
            existing_columns = {row[0] for row in result.fetchall()}
            logger.info(f"📋 Found existing columns: {sorted(existing_columns)}")
            
            # Rename columns that exist
            renamed_count = 0
            for old_name, new_name in column_mappings.items():
                if old_name in existing_columns and new_name not in existing_columns:
                    logger.info(f"🔄 Renaming column: {old_name} -> {new_name}")
                    
                    connection.execute(text(f"""
                        ALTER TABLE feedback 
                        RENAME COLUMN {old_name} TO {new_name}
                    """))
                    
                    renamed_count += 1
                    logger.info(f"✅ Renamed {old_name} to {new_name}")
                    
                elif new_name in existing_columns:
                    logger.info(f"⏭️ Column {new_name} already exists, skipping {old_name}")
                    
                else:
                    logger.warning(f"⚠️ Column {old_name} not found in table")
            
            # Commit the transaction
            connection.commit()
            
            logger.info(f"🎉 Migration completed successfully!")
            logger.info(f"📊 Renamed {renamed_count} columns")
            
            # Verify final column names
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'feedback'
                ORDER BY column_name
            """))
            
            final_columns = [row[0] for row in result.fetchall()]
            logger.info(f"📋 Final columns: {final_columns}")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate_feedback_columns()
