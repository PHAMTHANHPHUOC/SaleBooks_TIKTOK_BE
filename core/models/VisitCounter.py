# models.py
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Q
import json

class VisitCounter(models.Model):
    page_name = models.CharField(max_length=100, unique=True, default='homepage')
    total_visits = models.IntegerField(default=0)
    today_visits = models.IntegerField(default=0)
    last_visit_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'visit_counter'
    
    def __str__(self):
        return f"{self.page_name}: {self.total_visits} visits"

class VisitLog(models.Model):
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    page_visited = models.CharField(max_length=100)
    visit_time = models.DateTimeField(auto_now_add=True)
    
    # Thêm các trường mới để hỗ trợ frontend
    country_code = models.CharField(max_length=2, null=True, blank=True)
    country_name = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    referrer = models.URLField(null=True, blank=True)
    screen_resolution = models.CharField(max_length=20, null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = 'visit_logs'
        indexes = [
            models.Index(fields=['visit_time', 'country_code']),
            models.Index(fields=['visit_time', 'page_visited']),
            models.Index(fields=['ip_address', 'visit_time']),
        ]
    
    def __str__(self):
        return f"{self.ip_address} - {self.page_visited} - {self.visit_time}"

    @classmethod
    def get_stats_for_period(cls, period='today', page='homepage'):
        """Lấy thống kê theo khoảng thời gian"""
        now = timezone.now()
        
        if period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        else:  # all time
            return cls.objects.filter(page_visited=page)
        
        return cls.objects.filter(
            page_visited=page,
            visit_time__gte=start_date,
            visit_time__lte=end_date
        )
    
    @classmethod
    def get_country_stats(cls, period='today', page='homepage'):
        """Lấy thống kê theo quốc gia"""
        queryset = cls.get_stats_for_period(period, page)
        
        return queryset.values('country_code', 'country_name').annotate(
            visits=Count('id')
        ).exclude(
            country_code__isnull=True
        ).order_by('-visits')
    
    @classmethod
    def get_hourly_stats(cls, page='homepage'):
        """Lấy thống kê theo giờ (24h qua)"""
        now = timezone.now()
        start_time = now - timedelta(hours=24)
        
        from django.db.models import Extract
        
        return cls.objects.filter(
            page_visited=page,
            visit_time__gte=start_time
        ).extra(
            select={'hour': 'EXTRACT(hour FROM visit_time)'}
        ).values('hour').annotate(
            visits=Count('id')
        ).order_by('hour')
    
    @classmethod
    def get_daily_stats(cls, page='homepage'):
        """Lấy thống kê theo ngày (7 ngày qua)"""
        now = timezone.now()
        start_time = now - timedelta(days=7)
        
        from django.db.models import Extract
        
        return cls.objects.filter(
            page_visited=page,
            visit_time__gte=start_time
        ).extra(
            select={'date': 'DATE(visit_time)'}
        ).values('date').annotate(
            visits=Count('id')
        ).order_by('date')
    
    @classmethod
    def get_unique_visitors_today(cls, page='homepage'):
        """Lấy số lượng visitor duy nhất hôm nay"""
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        return cls.objects.filter(
            page_visited=page,
            visit_time__gte=today
        ).values('ip_address').distinct().count()
    
    @classmethod
    def calculate_growth(cls, page='homepage'):
        """Tính toán tăng trưởng"""
        now = timezone.now()
        
        # Hôm nay vs hôm qua
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        yesterday_end = today_start
        
        today_visits = cls.objects.filter(
            page_visited=page,
            visit_time__gte=today_start
        ).count()
        
        yesterday_visits = cls.objects.filter(
            page_visited=page,
            visit_time__gte=yesterday_start,
            visit_time__lt=yesterday_end
        ).count()
        
        # Tuần này vs tuần trước
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        last_week_start = week_start - timedelta(days=7)
        last_week_end = week_start
        
        this_week_visits = cls.objects.filter(
            page_visited=page,
            visit_time__gte=week_start
        ).count()
        
        last_week_visits = cls.objects.filter(
            page_visited=page,
            visit_time__gte=last_week_start,
            visit_time__lt=last_week_end
        ).count()
        
        # Tháng này vs tháng trước
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_start.month == 1:
            last_month_start = month_start.replace(year=month_start.year-1, month=12)
        else:
            last_month_start = month_start.replace(month=month_start.month-1)
        
        this_month_visits = cls.objects.filter(
            page_visited=page,
            visit_time__gte=month_start
        ).count()
        
        last_month_visits = cls.objects.filter(
            page_visited=page,
            visit_time__gte=last_month_start,
            visit_time__lt=month_start
        ).count()
        
        # Tính phần trăm tăng trưởng
        def calculate_percentage(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100)
        
        return {
            'today_vs_yesterday': calculate_percentage(today_visits, yesterday_visits),
            'this_week_vs_last_week': calculate_percentage(this_week_visits, last_week_visits),
            'this_month_vs_last_month': calculate_percentage(this_month_visits, last_month_visits)
        }