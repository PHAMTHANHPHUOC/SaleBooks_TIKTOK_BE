from apscheduler.schedulers.blocking import BlockingScheduler
from core.views.cron import call_api

def start():
    scheduler = BlockingScheduler()
    
    # Gọi API mỗi ngày lúc 00:00
    scheduler.add_job(call_api, 'cron', hour=0, minute=0)
    
    print("✅ Scheduler started. Job will run daily at 00:00.")
    scheduler.start()

