import os

from dotenv import load_dotenv
from supabase import create_client


def _print(message: str) -> None:
    print(message.encode("ascii", errors="replace").decode("ascii"))


def verify():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        _print("ERROR Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return False

    client = create_client(url, key)

    _print("Checking 'documents' table...")
    try:
        client.table("documents").select("id", count="exact").limit(1).execute()
        _print("OK Table 'documents' exists.")
    except Exception as e:
        _print(f"ERROR Table 'documents' NOT FOUND: {e}")
        return False

    _print("Checking 'match_documents' function...")
    try:
        dummy_embedding = [0.0] * 384
        client.rpc(
            "match_documents",
            {
                "query_embedding": dummy_embedding,
                "match_count": 1,
            },
        ).execute()
        _print("OK Function 'match_documents' exists.")
    except Exception as e:
        _print(f"ERROR Function 'match_documents' NOT FOUND: {e}")
        return False

    _print("Database is READY for ingestion.")
    return True


if __name__ == "__main__":
    verify()
