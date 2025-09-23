from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from apscheduler.schedulers.background import BackgroundScheduler
        from .views.cron import call_api

        scheduler = BackgroundScheduler()
        # test giờ cụ thể
        scheduler.add_job(call_api, 'cron', hour=0, minute=00) 
        # production thì đổi thành (hour=0, minute=0) -> chạy 00:00
        scheduler.start()
