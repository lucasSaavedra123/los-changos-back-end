from apscheduler.schedulers.background import BackgroundScheduler
from .tasks import notify_expiration_expenses


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(notify_expiration_expenses, trigger='cron', hour='15', minute='0')
    scheduler.start()
