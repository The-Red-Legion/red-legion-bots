#!/usr/bin/env python3
"""
Simple test to validate URL encoding is working correctly
This can be run on the production server to verify the fix
"""
import sys
import os

def test_url_encoding():
    """Test that URL encoding is working correctly"""
    print("🧪 Testing URL encoding fix...")
    
    try:
        # Add the project root to the path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        sys.path.insert(0, project_root)
        
        from src.config.settings import get_database_url
        
        database_url = get_database_url()
        print(f"✅ Database URL obtained successfully")
        print(f"📋 URL (first 50 chars): {database_url[:50]}...")
        
        # Check for unencoded special characters that would cause parsing errors
        has_unencoded_hash = '#' in database_url
        has_unencoded_ampersand = '&' in database_url and '%26' not in database_url
        has_unencoded_lt = '<' in database_url and '%3C' not in database_url
        has_unencoded_gt = '>' in database_url and '%3E' not in database_url
        has_unencoded_asterisk = '*' in database_url and '%2A' not in database_url
        
        # Check for properly encoded characters
        has_encoded_hash = '%23' in database_url
        has_encoded_ampersand = '%26' in database_url
        has_encoded_lt = '%3C' in database_url
        has_encoded_gt = '%3E' in database_url
        has_encoded_asterisk = '%2A' in database_url
        
        print(f"🔍 Unencoded '#': {has_unencoded_hash}")
        print(f"🔍 Unencoded '&': {has_unencoded_ampersand}")
        print(f"🔍 Unencoded '<': {has_unencoded_lt}")
        print(f"🔍 Unencoded '>': {has_unencoded_gt}")
        print(f"🔍 Unencoded '*': {has_unencoded_asterisk}")
        
        print(f"✅ Encoded '#' (%23): {has_encoded_hash}")
        print(f"✅ Encoded '&' (%26): {has_encoded_ampersand}")
        print(f"✅ Encoded '<' (%3C): {has_encoded_lt}")
        print(f"✅ Encoded '>' (%3E): {has_encoded_gt}")
        print(f"✅ Encoded '*' (%2A): {has_encoded_asterisk}")
        
        # Overall assessment
        has_any_unencoded = (has_unencoded_hash or has_unencoded_ampersand or 
                           has_unencoded_lt or has_unencoded_gt or has_unencoded_asterisk)
        
        if has_any_unencoded:
            print("❌ URL encoding FAILED - unencoded special characters detected!")
            print("💡 This would cause 'invalid dsn' parsing errors")
            return False
        else:
            print("✅ URL encoding PASSED - all special characters properly encoded!")
            print("💡 Database URL should parse correctly")
            return True
            
    except ModuleNotFoundError as e:
        print(f"❌ Module import failed: {e}")
        print("💡 This suggests the application code is not properly deployed")
        return False
    except Exception as e:
        print(f"❌ URL encoding test failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return False

def main():
    """Main test function"""
    print("🧪 Starting URL encoding validation...")
    print(f"🏠 Working directory: {os.getcwd()}")
    
    success = test_url_encoding()
    
    if success:
        print("🎉 URL encoding validation PASSED!")
        print("💡 Ready for deployment - database parsing errors should be resolved")
        sys.exit(0)
    else:
        print("❌ URL encoding validation FAILED!")
        print("💡 Database parsing errors will still occur")
        sys.exit(1)

if __name__ == "__main__":
    main()
