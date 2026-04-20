import requests
import json

# The URL where your reminder_app service is running (Port 8001)
URL = "http://localhost:8001/create-reminder"

def test_add_reminder():
    # Correct Request Body per ReminderRequest model
    payload = {
        "title": "Drink Water - AI Reminder",
        "date": "2026-04-20",
        "time": "22:03"
    }

    print(f"Sending request to {URL}...")
    try:
        response = requests.post(
            URL, 
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Success!")
            print("Response:", response.json())
        else:
            print(f"❌ Failed (Status: {response.status_code})")
            print("Detail:", response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_add_reminder()
