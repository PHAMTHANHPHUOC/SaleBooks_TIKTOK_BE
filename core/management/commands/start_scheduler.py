from django.core.management.base import BaseCommand
from core.scheduler import start

class Command(BaseCommand):
    help = 'Start the background scheduler'

    def handle(self, *args, **kwargs):
        start()

