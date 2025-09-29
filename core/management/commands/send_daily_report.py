from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import requests
import json
import logging
from core.views.view_teams_report import get_daily_stats, create_teams_message
from django.conf import settings
from core.views.view_teams_report import adapt_payload_for_webhook

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Gửi báo cáo thống kê hàng ngày vào Microsoft Teams'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Chạy ở chế độ test (không gửi thực tế)',
        )
        parser.add_argument(
            '--time',
            type=str,
            help='Thời gian gửi báo cáo (format: HH:MM)',
        )
        parser.add_argument(
            '--webhook-url',
            type=str,
            dest='webhook_url',
            help='Ghi đè URL webhook (ưu tiên hơn biến môi trường)',
        )
        parser.add_argument(
            '--type',
            type=str,
            dest='webhook_type',
            choices=['incoming', 'flow'],
            help='Kiểu webhook: incoming (Teams Incoming Webhook) hoặc flow (Power Automate)',
        )

    def handle(self, *args, **options):
        test_mode = options['test']
        report_time = options.get('time')
        override_webhook_url = (options.get('webhook_url') or '').strip()
        override_webhook_type = (options.get('webhook_type') or '').strip().lower()
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Bắt đầu gửi báo cáo thống kê...')
        )
        
        try:
            # Lấy thống kê
            stats = get_daily_stats()
            
            # Tạo message
            message = create_teams_message(stats)
            
            if test_mode:
                self.stdout.write(
                    self.style.WARNING('🧪 CHẠY Ở CHẾ ĐỘ TEST - Không gửi thực tế')
                )
                self.stdout.write('📊 Dữ liệu báo cáo:')
                self.stdout.write(f'  - Ngày: {stats["date"]}')
                self.stdout.write(f'  - Tổng lượt truy cập: {stats["visit_stats"]["total_visits"]:,}')
                self.stdout.write(f'  - Lượt truy cập hôm nay: {stats["visit_stats"]["today_visits"]:,}')
                self.stdout.write(f'  - Người dùng duy nhất: {stats["visit_stats"]["unique_today"]:,}')
                self.stdout.write(f'  - Số quốc gia: {len(stats["country_stats"])}')
                self.stdout.write(f'  - Top sản phẩm: {len(stats["top_products"])}')
                
                self.stdout.write('\n📤 Message sẽ được gửi:')
                self.stdout.write(json.dumps(message, indent=2, ensure_ascii=False))
                
                return
            
            # Gửi đến Teams
            webhook_url = (override_webhook_url
                           or getattr(settings, 'TEAMS_WEBHOOK_URL', '')).strip()
            webhook_type = (override_webhook_type
                            or getattr(settings, 'TEAMS_WEBHOOK_TYPE', '')).strip().lower()
            if not webhook_type:
                if 'webhook.office.com' in webhook_url or 'office.com/webhook' in webhook_url:
                    webhook_type = 'incoming'
                elif 'powerautomate' in webhook_url or 'flow.microsoft' in webhook_url or 'environment.api.powerplatform.com' in webhook_url:
                    webhook_type = 'flow'
                else:
                    webhook_type = 'incoming'

            if not webhook_url:
                self.stdout.write(self.style.ERROR('❌ Chưa cấu hình TEAMS_WEBHOOK_URL và không truyền --webhook-url'))
                return

            payload = adapt_payload_for_webhook(message, webhook_type)

            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code in (200,202):
                self.stdout.write(
                    self.style.SUCCESS('✅ Báo cáo đã được gửi thành công đến Microsoft Teams!')
                )
                self.stdout.write(f'📊 Thống kê gửi:')
                self.stdout.write(f'  - Ngày: {stats["date"]}')
                self.stdout.write(f'  - Tổng lượt truy cập: {stats["visit_stats"]["total_visits"]:,}')
                self.stdout.write(f'  - Lượt truy cập hôm nay: {stats["visit_stats"]["today_visits"]:,}')
                self.stdout.write(f'  - Người dùng duy nhất: {stats["visit_stats"]["unique_today"]:,}')
                self.stdout.write(f'  - Số quốc gia: {len(stats["country_stats"])}')
                self.stdout.write(f'  - Top sản phẩm: {len(stats["top_products"])}')
                
                logger.info(f"Báo cáo hàng ngày đã được gửi thành công - {stats['date']}")
                
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Lỗi khi gửi báo cáo: {response.status_code}')
                )
                self.stdout.write(f'Chi tiết lỗi: {response.text}')
                logger.error(f"Lỗi khi gửi báo cáo: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Lỗi kết nối: {str(e)}')
            )
            logger.error(f"Lỗi kết nối khi gửi báo cáo: {str(e)}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Lỗi không xác định: {str(e)}')
            )
            logger.error(f"Lỗi không xác định khi gửi báo cáo: {str(e)}")
