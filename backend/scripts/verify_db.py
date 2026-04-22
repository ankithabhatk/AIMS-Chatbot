import os
from dotenv import load_dotenv
from supabase import create_client

def verify():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return False
        
    client = create_client(url, key)
    
    # Check table
    print("Checking 'documents' table...")
    try:
        res = client.table("documents").select("id", count="exact").limit(1).execute()
        print(f"✅ Table 'documents' exists.")
    except Exception as e:
        print(f"❌ Table 'documents' NOT FOUND: {e}")
        return False
        
    # Check RPC
    print("Checking 'match_documents' function...")
    try:
        # Mock search with zero vector
        dummy_embedding = [0.0] * 384
        res = client.rpc("match_documents", {
            "query_embedding": dummy_embedding,
            "match_count": 1
        }).execute()
        print(f"✅ Function 'match_documents' exists.")
    except Exception as e:
        print(f"❌ Function 'match_documents' NOT FOUND: {e}")
        return False
        
    print("\n🚀 Database is READY for ingestion.")
    return True

if __name__ == "__main__":
    verify()
