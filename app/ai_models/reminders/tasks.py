from app.ai_models.reminders.celery_config import celery_app
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

@celery_app.task
def remind_user(user_id, message):
    try:
        import sys
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"DEBUG [{now}]: Firing reminder for {user_id}: {message}")
        sys.stdout.flush()
        r.lpush(f"notifications:{user_id}", message)
        print(f"DEBUG [{now}]: Done! Pushed to Redis for key notifications:{user_id}")
        sys.stdout.flush()
    except Exception as e:
        print(f"ERROR in remind_user: {str(e)}")
        raise e