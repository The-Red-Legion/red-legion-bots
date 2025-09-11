#!/usr/bin/env python3
"""
Database Schema Inspector
Connects to the Red Legion database and examines current structure
"""

import os
import sys
import asyncio
import asyncpg
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def inspect_database():
    """Connect to database and inspect current schema"""
    try:
        # Try to get database URL from config
        try:
            from config import DATABASE_URL
            db_url = DATABASE_URL
            print(f"✅ Using DATABASE_URL from config")
        except ImportError:
            # Try environment variable
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                print("❌ No DATABASE_URL found in config or environment")
                return False
            print(f"✅ Using DATABASE_URL from environment")
        
        # Connect to database
        print(f"🔗 Connecting to database...")
        connection = await asyncpg.connect(db_url)
        print(f"✅ Connected successfully!")
        
        # Get all tables
        tables_query = """
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """
        
        tables = await connection.fetch(tables_query)
        
        print(f"\n📊 Current Database Tables ({len(tables)} found):")
        print("=" * 50)
        
        for table in tables:
            print(f"  • {table['table_name']} ({table['table_type']})")
        
        # Get detailed info for each table
        print(f"\n🔍 Table Details:")
        print("=" * 50)
        
        for table in tables:
            table_name = table['table_name']
            
            # Get column information
            columns_query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position;
            """
            
            columns = await connection.fetch(columns_query, table_name)
            
            print(f"\n📋 {table_name} ({len(columns)} columns):")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"    {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        # Get indexes
        indexes_query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
        """
        
        indexes = await connection.fetch(indexes_query)
        
        print(f"\n🗂️ Indexes ({len(indexes)} found):")
        print("=" * 50)
        
        current_table = None
        for idx in indexes:
            if idx['tablename'] != current_table:
                current_table = idx['tablename']
                print(f"\n📋 {current_table}:")
            print(f"    • {idx['indexname']}")
        
        # Get foreign keys
        fk_query = """
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
            ORDER BY tc.table_name, kcu.column_name;
        """
        
        foreign_keys = await connection.fetch(fk_query)
        
        print(f"\n🔗 Foreign Key Relationships ({len(foreign_keys)} found):")
        print("=" * 50)
        
        for fk in foreign_keys:
            print(f"  {fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        await connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(inspect_database())
    if not success:
        sys.exit(1)
