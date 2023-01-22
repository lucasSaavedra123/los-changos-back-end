from apscheduler.schedulers.background import BackgroundScheduler
from .tasks import notify_expiration_expenses


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(notify_expiration_expenses, trigger='cron', hour='14', minute='57')
    scheduler.start()
