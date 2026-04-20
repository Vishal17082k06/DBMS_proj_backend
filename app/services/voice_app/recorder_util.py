import speech_recognition as sr
import requests
import os
import threading

# Configuration
SERVER_URL = "http://localhost:8003/transcribe"

LOCK = threading.Lock()

# Global state to share with Frontend UI via FastAPI
IS_RECORDING = False
IS_SUMMARIZING = False

def record_and_transcribe(interaction_id: int = None):
    """
    Listens until the user stops talking, then sends the audio to the server.
    Updates the database interaction if interaction_id is provided.
    """
    global IS_RECORDING, IS_SUMMARIZING
    
    # Pre-check: Don't start if already active
    if not LOCK.acquire(blocking=False):
        return
    
    try:
        recognizer = sr.Recognizer()
        recognizer.pause_threshold = 5.0  # Wait for 5 seconds of silence before finishing
        
        with sr.Microphone() as source:
            print("🎤 Adjusting for ambient noise... Please wait.")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
            print("🎙️ Listening... (Stop talking for 5s to finish)")
            IS_RECORDING = True
            try:
                # listens until 5 seconds of silence is detected
                audio_data = recognizer.listen(source, timeout=10, phrase_time_limit=None)
                
                # Save the captured audio locally
                IS_RECORDING = False
                IS_SUMMARIZING = True
                
                filename = "temp_recording.wav"
                with open(filename, "wb") as f:
                    f.write(audio_data.get_wav_data())
                
                print("📤 Transcribing audio locally...")
                try:
                    from app.services.voice_app.transcription_service import transcribe_audio
                except ImportError:
                    print(f"❌ Could not import transcription_service")
                    return None
                
                text = transcribe_audio(filename)

                if text:
                    print(f"✅ Transcribed: {text}")
                    
                    try:
                        from app.services.conversation_summarizer import analyze_conversation
                        import json
                        analysis = analyze_conversation(text)
                        print("\n💡 COMBINED JSON RESULT:")
                        print(json.dumps(analysis, indent=2))
                        
                        # Update database with real conversation and summary
                        summary = analysis.get("summary", "Summarization complete.")
                        if interaction_id:
                            try:
                                from app.database.db import update_conversation_results
                                update_conversation_results(interaction_id, text, summary)
                                print(f"✅ Database updated for Interaction {interaction_id}")
                            except Exception as db_err:
                                print(f"❌ Could not update DB: {db_err}")

                        # Ensure calendar sync - only call if valid events are present
                        events_list = analysis.get("events", [])
                        if isinstance(events_list, list) and len(events_list) > 0:
                            import requests
                            for event in events_list:
                                if not isinstance(event, dict): continue
                                    
                                title = event.get("title")
                                date  = event.get("date")
                                time  = event.get("time")

                                if title and date and time:
                                    try:
                                        print(f"🚀 Pushing Reminder to Calendar: {title}")
                                        requests.post("http://localhost:8001/create-reminder", json=event, timeout=5)
                                    except Exception as sync_err:
                                        print(f"❌ Could not sync reminder {title} to Calendar | Error: {sync_err}")
                                else:
                                    print(f"⚠️ Skipping incomplete event: {event}")
                        else:
                            print("ℹ️ No relevant calendar events found to sync.")
                            
                    except Exception as e:
                        print(f"❌ Summarization/Sync failed: {e}")
                    
                    return text
                else:
                    print("ℹ️ Transcription was empty (likely silence).")
                    return None
            
            except sr.WaitTimeoutError:
                print("⏳ No speech detected (Timeout).")
                return None
            except Exception as e:
                print(f"❌ Error: {e}")
                return None
    finally:
        IS_RECORDING = False
        IS_SUMMARIZING = False
        LOCK.release()
        if os.path.exists("temp_recording.wav"):
            os.remove("temp_recording.wav")

if __name__ == "__main__":
    # Test it
    record_and_transcribe()
