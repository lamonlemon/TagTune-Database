import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Get absolute path for base_prompt.txt
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPT_PATH = os.path.join(BASE_DIR, "base_prompt.txt")
GEMINI_OUTPUT_PATH = os.path.join(BASE_DIR, "gemini_output.json")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def analyze_songs(batch_data):
    """
    batch_data: A list of dicts: [{"index": 101, "text": "Title - Artist"}, ...]
    Returns: A list of dictionaries matching the required JSON structure.
    """
    # Load base prompt
    if not os.path.exists(PROMPT_PATH):
        print(f"Error: {PROMPT_PATH} not found.")
        return []
        
    with open(PROMPT_PATH, "r") as f:
        base_prompt = f.read()

    # Form input section using the REAL indices
    input_text = "\n".join([f"{item['index']}. {item['text']}" for item in batch_data])
    
    # Construct final prompt
    final_prompt = base_prompt.replace("inputonhere", input_text)

    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=final_prompt
        )
        
        text = response.text.strip()
        
        # Remove markdown code blocks if AI ignored the "no markdown" rule
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        result_json = json.loads(text)
        
        # Save raw AI output for debugging (as a proper JSON object)
        with open(GEMINI_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(result_json, f, indent=2, ensure_ascii=False)
            
        return result_json
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return []

if __name__ == "__main__":
    test_batch = [
        {"index": 101, "text": "Seven - Jung Kook"},
        {"index": 102, "text": "만남은 쉽고 이별은 어려워 - 베이식"}
    ]
    print(analyze_songs(test_batch))