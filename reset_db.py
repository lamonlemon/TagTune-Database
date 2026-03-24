import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SECRET_KEY")

if not url or not key:
    print("SUPABASE_URL and SUPABASE_SECRET_KEY must be set in .env")
    exit(1)

supabase: Client = create_client(url, key)

def reset_tables():
    print("Resetting database AND ID counters (excluding genres)...")

    try:
        # In Supabase/PostgreSQL, you cannot wipe IDs via standard DELETE.
        # We must call an RPC (Remote Procedure Call) that runs TRUNCATE with RESTART IDENTITY.
        # NOTE: You MUST create this function in the Supabase SQL Editor first WITH SECURITY DEFINER
        supabase.rpc("reset_database_except_genres").execute()
        
        print("Database reset successfully. Only 'genres' table remains untouched and all other IDs now start at 1.")
    except Exception as e:
        print(f"Error resetting tables via RPC: {e}")
        print("\n" + "="*70)
        print("⚠️ CONFIGURE YOUR SUPABASE FUNCTION PROPERLY!")
        print("Because of Permissions (Error 42501), you must add SECURITY DEFINER to your function.")
        print("Copy and paste this into your Supabase Dashboard -> SQL Editor and run it:\n")
        print('''CREATE OR REPLACE FUNCTION reset_database_except_genres()
RETURNS void 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  TRUNCATE TABLE 
    song_genres, 
    song_featuring, 
    song_producers, 
    songs, 
    albums, 
    groups, 
    artists 
  RESTART IDENTITY CASCADE;
END;
$$;''')
        print("="*70 + "\n")

if __name__ == "__main__":
    reset_tables()
