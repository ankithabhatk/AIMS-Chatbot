#!/usr/bin/env python3
"""
Test Supabase Database Connection
Verifies that the database can be reached and is properly configured
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from sqlalchemy import create_engine, text, event
from sqlalchemy.pool import QueuePool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test database connection"""
    
    from app.config import get_settings
    
    settings = get_settings()
    db_url = settings.database_url
    
    print("\n" + "="*80)
    print("🗄️  SUPABASE DATABASE CONNECTION TEST")
    print("="*80 + "\n")
    
    # Check if password is set
    if "[YOUR-PASSWORD]" in db_url:
        print("❌ ERROR: Database URL contains placeholder '[YOUR-PASSWORD]'")
        print("\n📝 You need to:")
        print("   1. Find your Supabase database password")
        print("   2. Update backend/.env with actual password")
        print("   3. Replace [YOUR-PASSWORD] in DATABASE_URL")
        print("\nFormat: postgresql://postgres:[PASSWORD]@db.opswmwtrweqhqkuagbqr.supabase.co:5432/postgres\n")
        return False
    
    print("📊 Connection Configuration:")
    print(f"   Database URL: {db_url}")
    if settings.supabase_url:
        print(f"   Supabase URL: {settings.supabase_url}")
    print(f"\n🔗 Attempting connection...\n")
    
    try:
        # Create engine
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10}
        )
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            
            print("✅ CONNECTION SUCCESSFUL!\n")
            print(f"📈 PostgreSQL Version: {version}\n")
            
            # Get database info
            result = connection.execute(text("""
                SELECT datname, pg_database.datdba, 
                       pg_size_pretty(pg_database_size(datname)) as size
                FROM pg_database 
                WHERE datname = 'postgres'
            """))
            db_info = result.fetchone()
            if db_info:
                print(f"📊 Database Info:")
                print(f"   Name: {db_info[0]}")
                print(f"   Size: {db_info[2]}")
            
            # Test table creation ability
            try:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS connection_test (
                        id SERIAL PRIMARY KEY,
                        test_value VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                connection.commit()
                print(f"\n✅ Table creation: SUCCESS")
                
                # Clean up
                connection.execute(text("DROP TABLE IF EXISTS connection_test"))
                connection.commit()
                
            except Exception as e:
                print(f"\n⚠️  Table operations may be restricted: {str(e)[:100]}")
        
        engine.dispose()
        
        print("\n" + "="*80)
        print("✅ DATABASE IS PROPERLY CONFIGURED AND CONNECTED")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"❌ CONNECTION FAILED\n")
        print(f"Error: {str(e)}\n")
        
        print("🔍 Troubleshooting:")
        if "password" in str(e).lower():
            print("   • Check if password is correct")
            print("   • Verify you've replaced [YOUR-PASSWORD] with actual password")
        elif "refused" in str(e).lower():
            print("   • Database server may be offline")
            print("   • Check internet connection")
            print("   • Verify Supabase project is active")
        elif "unknown host" in str(e).lower():
            print("   • Check database hostname")
            print("   • Verify it's: db.opswmwtrweqhqkuagbqr.supabase.co")
        
        print("\n" + "="*80)
        return False


def main():
    """Main entry point"""
    success = test_database_connection()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
