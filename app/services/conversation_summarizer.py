import json
import logging
import os
from typing import Dict, Any, Tuple
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

logger = logging.getLogger(__name__)

_openai_client = None

def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables.")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client

def analyze_conversation(transcript: str, current_time: datetime = None) -> Dict[str, Any]:
    """
    Analyzes a conversation transcript to:
    1. Generate a 3-5 line summary.
    2. Extract any discussed calendar events into specific JSON structures.
    
    Returns:
        Dict spanning the "summary" string and the "events" list.
    """
    if not transcript or not transcript.strip():
        return {"summary": "No conversation detected.", "events": []}

    if current_time is None:
        current_time = datetime.now()

    prompt = f"""
    You are an intelligent assistant analyzing a conversation transcript.
    Today's current date and time is: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
    
    Please read the following conversation:
    "{transcript}"

    Output EXACTLY a JSON object with two keys: "summary" and "events".
    
    1. "summary": Provide a 3 to 5 line summary of the conversation. 
    2. "events": A list of important events/appointments discussed. If there are none, return an empty list [].
    
    For each event in the "events" array, it MUST follow exactly this format (use 24-hour time):
    {{
      "title": "Meeting with team",
      "date": "2026-04-20",
      "time": "10:30"
    }}
    
    Only return valid JSON. Do not return markdown blocks like ```json
    """

    client = get_openai_client()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2, # Low temp for structured extraction
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        # Guarantee missing keys gracefully
        if "summary" not in data:
            data["summary"] = "No summary generated."
        if "events" not in data:
            data["events"] = []
            
        return data

    except Exception as e:
        logger.error(f"Failed to analyze conversation: {e}")
        return {"summary": "Failed to run summarization analysis due to an error.", "events": []}



# ==========================================
# Self-Test Execution Block
# ==========================================
if __name__ == "__main__":
    test_transcript = "Hey, it was great catching up. Let's make sure we sync with the engineering team tomorrow at 2 PM. Also, don't forget the dentist appointment on April 25th at 9:15 AM."
    
    print("\n--- Testing Conversation Analyzer ---")
    print(f"Transcript: {test_transcript}\n")
    
    try:
        result_data = analyze_conversation(test_transcript)
        
        print("💡 COMBINED JSON RESULT:")
        print(json.dumps(result_data, indent=2))
        
    except ValueError as e:
        print(f"❌ Error: {e}")
