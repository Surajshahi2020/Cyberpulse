# collect/views.py
from django.shortcuts import render
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from urllib.parse import quote
from django.db.models import Q  # 🔸 You were using Q but didn't import it!
from .models import ThreatAlert
from collections import Counter
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count
import json
from django.db.models.functions import TruncDate

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

    paginator = Paginator(threats, 4)
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
        image = request.FILES.get('image')  # 🔸 Get uploaded image

        if not title or not description:
            return render(request, 'news_add.html', {
                'alert_type': 'error',
                'alert_message': 'Title and Description are required.',
                'form_data': request.POST
            })

        severity = severity if severity in ['low', 'medium', 'high'] else 'medium'

        if not url:
            url = "https://example.com/placeholder"

        try:
            # 🔸 Create with image (can be None if not provided — but your form marks it required)
            ThreatAlert.objects.create(
                title=title,
                content=description,
                source=source,
                category = category,
                url=url,
                severity=severity,
                image=image  # 🔸 Save image
            )

            return render(request, 'news_add.html', {
                'alert_type': 'success',
                'alert_message': '✅ Threat report saved successfully!',
                # Optional: clear form by NOT sending form_data
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
    # Get high severity threats with all related data
    high_threats = ThreatAlert.objects.filter(severity='high').order_by('-timestamp')
    
    # Get recent medium threats
    medium_threats = ThreatAlert.objects.filter(severity='medium').order_by('-timestamp')[:5]
    
    # Combine both for the template
    all_critical_threats = list(high_threats) + list(medium_threats)
    
    # Add pagination
    paginator = Paginator(all_critical_threats, 3)  # Show 12 threats per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'newsTrending.html', {
        'threats': page_obj,  # Use paginated threats
        'high_threats': high_threats,
        'medium_threats': medium_threats,
        'total_high': high_threats.count(),
        'total_medium': medium_threats.count(),
        'total_threats': len(all_critical_threats),
        'page_obj': page_obj,  # For pagination controls
    })