from celery import Celery

celery_app = Celery(
    'reminders',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
    include=['app.ai_models.reminders.tasks']
)

celery_app.conf.update(
    timezone='Asia/Kolkata',
    enable_utc=True,
    task_track_started=True,
)