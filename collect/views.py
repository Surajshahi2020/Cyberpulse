# collect/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from urllib.parse import quote
from django.db.models import Q  # 🔸 You were using Q but didn't import it!
from .models import ThreatAlert, CurrentInformation, NewsSource
from collections import Counter
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count
import json
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import os

def dashboard(request):
    user = request.user
    role_map = {2: 'Admin', 1: 'Analyst', 0: 'Viewer'}
    role_display = role_map.get(getattr(user, 'role', 0), 'Unknown')

    query = request.GET.get('q', '').strip()
    threats = ThreatAlert.objects.all().order_by('-timestamp')  # 🔸 Usually newest first

    if query:
        threats = threats.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(source__icontains=query)
        )

    total_threats = threats.count()
    high_severity = threats.filter(severity='high').count()
    medium_severity = threats.filter(severity='medium').count()
    low_severity = threats.filter(severity='low').count()

    paginator = Paginator(threats, 5)
    page_number = request.GET.get('page')
    threats_page = paginator.get_page(page_number)

    return render(request, 'dashboard.html', {
        'threats': threats_page,
        'total_threats': total_threats,
        'high_severity': high_severity,
        'medium_severity': medium_severity,
        'low_severity': low_severity,
        'role_display': role_display,
    })


def newsfeeding(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        source = request.POST.get('source', 'unknown').strip()
        category = request.POST.get('category', 'unknown').strip()
        description = request.POST.get('description', '').strip()
        url = request.POST.get('url', '').strip()
        severity = request.POST.get('severity', 'medium').lower()
        image = request.FILES.get('image')
        video = request.FILES.get('video')

        # Validation
        if not title or not description:
            return render(request, 'news_add.html', {
                'alert_type': 'error',
                'alert_message': 'Title and Description are required.',
                'form_data': request.POST
            })

        # Validate severity
        valid_severities = ['low', 'medium', 'high', 'critical']
        severity = severity if severity in valid_severities else 'medium'

        # Validate URL
        if not url:
            url = "https://example.com/placeholder"

        # File validation
        errors = []
        
        if image:
            # Validate image size (10MB max)
            if image.size > 10 * 1024 * 1024:
                errors.append("Image size must be less than 10MB")
            
            # Validate image extension
            valid_image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in valid_image_extensions:
                errors.append("Invalid image format. Supported: JPG, JPEG, PNG, GIF")

        if video:
            # Validate video size (100MB max)
            if video.size > 100 * 1024 * 1024:
                errors.append("Video size must be less than 100MB")
            
            # Validate video extension
            valid_video_extensions = ['.mp4', '.mov', '.avi', '.webm', '.mkv']
            ext = os.path.splitext(video.name)[1].lower()
            if ext not in valid_video_extensions:
                errors.append("Invalid video format. Supported: MP4, MOV, AVI, WebM, MKV")

        # if image and video:
        #     errors.append("Please upload either an image OR a video, not both.")

        if errors:
            return render(request, 'news_add.html', {
                'alert_type': 'error',
                'alert_message': ' | '.join(errors),
                'form_data': request.POST
            })

        try:
            # Create threat alert
            threat_alert = ThreatAlert.objects.create(
                title=title,
                content=description,
                source=source,
                category=category,
                url=url,
                severity=severity,
                image=image,
                video=video
            )

            return render(request, 'news_add.html', {
                'alert_type': 'success',
                'alert_message': f'✅ Threat report #{threat_alert.id} saved successfully!',
            })

        except Exception as e:
            return render(request, 'news_add.html', {
                'alert_type': 'error',
                'alert_message': f'⚠️ Failed to save: {str(e)}',
                'form_data': request.POST
            })

    # GET request
    return render(request, 'news_add.html')


def newsSearching(request):
    selected = request.GET.getlist('category')
    threats = ThreatAlert.objects.all()
    if selected:
        threats = threats.filter(category__in=selected)
    threats = threats.order_by('-timestamp')

    # 🔢 Chart data (use full queryset, not paginated)
    category_counts = Counter(threats.values_list('category', flat=True))
    chart_data = []
    for value, label in ThreatAlert.CATEGORY_CHOICES:
        if not selected or value in selected:
            chart_data.append({
                'label': label,
                'count': category_counts.get(value, 0)
            })

    # 📄 Paginate (10 items per page)
    paginator = Paginator(threats, 3)
    page_number = request.GET.get('page')
    threats_page = paginator.get_page(page_number)

    return render(request, 'searchNews.html', {
        'threats': threats_page,  # ← paginated object
        'all_categories': ThreatAlert.CATEGORY_CHOICES,
        'selected_categories': selected,
        'chart_data': chart_data,
    })

def newsVisualization(request):
    # Get all threats
    threats = ThreatAlert.objects.all().order_by('-timestamp')

    # Total counts
    total_threats = threats.count()
    high_severity = threats.filter(severity='high').count()
    medium_severity = threats.filter(severity='medium').count()
    low_severity = threats.filter(severity='low').count()

    # Category distribution for chart
    category_data = threats.values('category').annotate(
        count=Count('id')
    ).order_by('-count')

    # Prepare chart data
    category_labels = []
    category_counts = []
    for item in category_data:
        label = dict(ThreatAlert.CATEGORY_CHOICES).get(item['category'], item['category'])
        category_labels.append(label)
        category_counts.append(item['count'])

    # Severity distribution for chart
    severity_data = threats.values('severity').annotate(
        count=Count('id')
    ).order_by('severity')

    severity_labels = []
    severity_counts = []
    for item in severity_data:
        label = dict(ThreatAlert.SEVERITY_CHOICES).get(item['severity'], item['severity'])
        severity_labels.append(label)
        severity_counts.append(item['count'])

    # Timeline data (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Simple manual approach for timeline data
    date_counts = {}
    for i in range(30):
        date = (timezone.now() - timedelta(days=i)).date()
        date_counts[date] = 0
    
    # Count threats for each date
    for threat in threats.filter(timestamp__gte=thirty_days_ago):
        threat_date = threat.timestamp.date()
        if threat_date in date_counts:
            date_counts[threat_date] += 1
    
    # Convert to sorted lists
    sorted_dates = sorted(date_counts.keys())
    timeline_labels = [date.strftime('%m/%d') for date in sorted_dates]
    timeline_counts = [date_counts[date] for date in sorted_dates]

    # Threat sources from the source field (much simpler!)
    sources_data = threats.values('source').annotate(
        count=Count('id')
    ).order_by('-count')[:10]  # Top 10 sources

    sources_labels = []
    sources_counts = []
    for item in sources_data:
        source_name = item['source'] if item['source'] else 'Unknown'
        sources_labels.append(source_name)
        sources_counts.append(item['count'])

    # Trend data (last 7 days by severity)
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    # Get dates for last 7 days
    dates = [(timezone.now() - timedelta(days=i)).date() for i in range(6, -1, -1)]
    trend_labels = [date.strftime('%m/%d') for date in dates]
    
    # Initialize trend data structure
    trend_data = {
        'high': [0] * 7,
        'medium': [0] * 7,
        'low': [0] * 7
    }
    
    # Get threat counts for each severity for last 7 days
    for i, date in enumerate(dates):
        day_start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(date, datetime.max.time()))
        
        day_threats = threats.filter(timestamp__range=(day_start, day_end))
        
        trend_data['high'][i] = day_threats.filter(severity='high').count()
        trend_data['medium'][i] = day_threats.filter(severity='medium').count()
        trend_data['low'][i] = day_threats.filter(severity='low').count()

    return render(request, 'newsVisualization.html', {
        'threats': threats[:10],
        'total_threats': total_threats,
        'high_severity': high_severity,
        'medium_severity': medium_severity,
        'low_severity': low_severity,
        'chart_labels': category_labels,
        'chart_data': category_counts,
        'severity_labels': severity_labels,
        'severity_data': severity_counts,
        'timeline_labels': timeline_labels,
        'timeline_data': timeline_counts,
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'sources_labels': sources_labels,
        'sources_data': sources_counts,
    })


def newsTrending(request):
    # Get critical threats with videos
    critical_threats_with_videos = ThreatAlert.objects.filter(
        severity='critical'
    ).exclude(
        video__isnull=True
    ).exclude(
        video=''
    ).order_by('-timestamp')
    
    # Get all threats with videos for statistics
    all_threats_with_videos = ThreatAlert.objects.exclude(
        video__isnull=True
    ).exclude(
        video=''
    )
    
    # Add pagination for critical threats with videos
    paginator = Paginator(critical_threats_with_videos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'newsTrending.html', {
        'threats': page_obj,
        'critical_threats': critical_threats_with_videos,
        'total_critical_with_videos': critical_threats_with_videos.count(),
        'total_all_videos': all_threats_with_videos.count(),
        'page_obj': page_obj,
    })


def newsReport(request):
    return render(request, 'news_report.html', {
    })


def newsCurrent(request):
    current_info_list = CurrentInformation.objects.all().order_by('-created_at')
    paginator = Paginator(current_info_list, 7)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'newsCurrent.html', {'page_obj': page_obj})


def newsSpy(request):
    """Combined view: list + manual form submission with alert context"""
    if request.method == 'POST':
        # Extract and clean data
        timing = request.POST.get('timing', '').strip()
        location = request.POST.get('location', '').strip()
        leader = request.POST.get('leader', '').strip()
        number = request.POST.get('number', '').strip() or None
        vehicle = request.POST.get('vehicle', '').strip() or None
        description = request.POST.get('description', '').strip() or None
        status = request.POST.get('status', 'pending').strip()

        # 🔒 Validation: Required fields
        if not timing or not location or not leader:
            current_info_list = CurrentInformation.objects.all().order_by('-created_at')
            paginator = Paginator(current_info_list, 7)
            page_obj = paginator.get_page(request.GET.get('page'))
            return render(request, 'newsSpy.html', {
                'alert_type': 'error',
                'alert_message': 'Timestamp, Location, and Field Leader are required.',
                'form_data': {
                    'timing': timing,
                    'location': location,
                    'leader': leader,
                    'number': number,
                    'vehicle': vehicle,
                    'description': description,
                    'status': status,
                },
                'page_obj': page_obj,
            })

        # 🔒 Validate status
        valid_statuses = ['pending', 'completed', 'cancelled']
        if status not in valid_statuses:
            status = 'pending'

        try:
            # ✅ Save to DB
            CurrentInformation.objects.create(
                timing=timing,
                location=location,
                leader=leader,
                number=number,
                vehicle=vehicle,
                description=description,
                status=status
            )
            # On success: redirect to avoid resubmission + show success
            current_info_list = CurrentInformation.objects.all().order_by('-created_at')
            paginator = Paginator(current_info_list, 7)
            page_obj = paginator.get_page(1)  # Go to page 1 to show new entry
            return render(request, 'newsSpy.html', {
                'alert_type': 'success',
                'alert_message': '✅ Intel report submitted successfully!',
                'page_obj': page_obj,
            })

        except Exception as e:
            current_info_list = CurrentInformation.objects.all().order_by('-created_at')
            paginator = Paginator(current_info_list, 7)
            page_obj = paginator.get_page(request.GET.get('page'))
            return render(request, 'newsSpy.html', {
                'alert_type': 'error',
                'alert_message': f'⚠️ Failed to save: {str(e)}',
                'form_data': {
                    'timing': timing,
                    'location': location,
                    'leader': leader,
                    'number': number,
                    'vehicle': vehicle,
                    'description': description,
                    'status': status,
                },
                'page_obj': page_obj,
            })

    # GET request
    current_info_list = CurrentInformation.objects.all().order_by('-created_at')
    paginator = Paginator(current_info_list, 7)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'newsSpy.html', {
        'page_obj': page_obj,
    })


def loginPage(request):
    return render(request, 'login.html', {
    })


def newsSource(request):
    search_query = request.GET.get('search', '').strip()
    
    sources = NewsSource.objects.all()
    
    if search_query:
        sources = sources.filter(
            name__icontains=search_query
        ) | sources.filter(
            url__icontains=search_query
        )
    
    sources = sources.order_by('name')
    
    # Pagination (12 per page – adjust as needed)
    paginator = Paginator(sources,12 )
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'newsSource.html', {
        'sources': page_obj,
        'search_query': search_query,
    })