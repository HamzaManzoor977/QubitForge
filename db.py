from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables immediately when this file is imported
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # This checks if the variables are actually loaded
    print("DEBUG: URL found?", bool(SUPABASE_URL))
    print("DEBUG: Key found?", bool(SUPABASE_KEY))
    raise RuntimeError("Supabase credentials not found in .env file")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_db():
    # Supabase handles schema automatically via the Dashboard
    pass

def save_history(topic, result, mode):
    try:
        supabase.table("research_history").insert({
            "topic": topic,
            "mode": mode,
            "result": result
        }).execute()
    except Exception as e:
        print(f"Error saving to DB: {e}")

def load_history():
    try:
        response = (
            supabase
            .table("research_history")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"Error loading from DB: {e}")
        return []

def clear_history():
    try:
        supabase.table("research_history").delete().neq("topic", "").execute()
    except Exception as e:
        print(f"Error clearing DB: {e}")