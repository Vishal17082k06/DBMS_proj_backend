import speech_recognition as sr
import requests
import os

# Configuration
SERVER_URL = "http://localhost:8003/transcribe"

# Global state to share with Frontend UI via FastAPI
IS_RECORDING = False
IS_SUMMARIZING = False

def record_and_transcribe():
    """
    Listens until the user stops talking, then sends the audio to the server.
    """
    global IS_RECORDING, IS_SUMMARIZING
    
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("🎤 Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        print("🎙️ Listening... (Stop talking to finish)")
        IS_RECORDING = True
        try:
            # listens until silence is detected
            audio_data = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            
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
                IS_SUMMARIZING = False
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
                    
                    # Ensure calendar sync
                    events_list = analysis.get("events", [])
                    if events_list:
                        import requests
                        for event in events_list:
                            try:
                                print(f"🚀 Pushing Reminder to Calendar: {event['title']}")
                                requests.post("http://localhost:8001/create-reminder", json=event, timeout=5)
                            except Exception as sync_err:
                                print(f"❌ Could not sync reminder {event['title']} to Calendar | Error: {sync_err}")
                    else:
                        print("ℹ️ No calendar events found in conversation.")
                        
                except Exception as e:
                    print(f"❌ Summarization failed: {e}")
                
                IS_SUMMARIZING = False
                return text
            else:
                print(f"❌ Failed to transcribe.")
                IS_SUMMARIZING = False
                return None
        
        except sr.WaitTimeoutError:
            print("⏳ No speech detected (Timeout).")
            IS_RECORDING = False
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            IS_RECORDING = False
            IS_SUMMARIZING = False
            return None
        finally:
            IS_RECORDING = False
            IS_SUMMARIZING = False
            if os.path.exists("temp_recording.wav"):
                os.remove("temp_recording.wav")

if __name__ == "__main__":
    # Test it
    record_and_transcribe()
