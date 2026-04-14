from flask import Blueprint, request, jsonify
from datetime import datetime
from app.ai_models.reminders.tasks import remind_user
import redis

reminder_bp = Blueprint('reminders', __name__)
r = redis.Redis(host='localhost', port=6379, db=0)

@reminder_bp.route('/schedule-reminder', methods=['POST'])
def schedule_reminder():
    data = request.json
    user_id = data['user_id']
    message = data['message']
    remind_at = datetime.fromisoformat(data['remind_at'])
    
    # Convert IST to UTC manually (IST is UTC + 5:30)
    # This ensures the task fires at the correct LOCAL time
    from datetime import timedelta
    remind_at_utc = remind_at - timedelta(hours=5, minutes=30)
    
    print(f"DEBUG: Local IST Target: {remind_at}")
    print(f"DEBUG: Internal UTC Target: {remind_at_utc}")
    
    remind_user.apply_async(args=[user_id, message], eta=remind_at_utc)
    return jsonify({"status": "Reminder scheduled", "at": str(remind_at)})


@reminder_bp.route('/get-notifications/<user_id>', methods=['GET'])
def get_notifications(user_id):
    msgs = []
    while True:
        item = r.rpop(f"notifications:{user_id}")
        if not item:
            break
        msgs.append(item.decode())
    return jsonify(msgs)