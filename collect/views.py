# collect/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from urllib.parse import quote  # 🔸 Required for URL encoding
from .models import ThreatAlert


def dashboard(request):
    user = request.user
    role_map = {2: 'Admin', 1: 'Analyst', 0: 'Viewer'}
    role_display = role_map.get(getattr(user, 'role', 0), 'Unknown')

    # 🔍 Get search query
    query = request.GET.get('q', '').strip()

    # 🗃️ Fetch real data from DB
    threats = ThreatAlert.objects.all().order_by('timestamp')

    # 🔍 Filter if search query exists
    if query:
        threats = threats.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(source__icontains=query)
        )

    # 📊 Calculate stats
    total_threats = threats.count()
    high_severity = threats.filter(severity='high').count()
    medium_severity = threats.filter(severity='medium').count()
    low_severity = threats.filter(severity='low').count()

    # 📄 Paginate results (8 per page)
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
        # Get form data
        title = request.POST.get('title', '').strip()
        source = request.POST.get('source', 'unknown').strip()
        description = request.POST.get('description', '').strip()
        url = request.POST.get('url', '').strip()
        severity = request.POST.get('severity', 'medium').lower()

        # Validate required fields
        if not title or not description:
            return render(request, 'news_add.html', {
                'alert_type': 'error',
                'alert_message': 'Title and Description are required.',
                'form_data': request.POST  # Repopulate form
            })

        # Normalize severity
        severity = severity if severity in ['low', 'medium', 'high'] else 'medium'

        try:
            # Handle empty URL
            if not url:
                url = "https://example.com/placeholder"

            ThreatAlert.objects.create(
                title=title,
                content=description,
                source=source,
                url=url,
                severity=severity
            )

            # ✅ SUCCESS: Render SAME page with success message
            return render(request, 'news_add.html', {
                'alert_type': 'success',
                'alert_message': '✅ Threat report saved successfully!',
                'form_data': request.POST  # Optional: keep form filled
            })

        except Exception as e:
            return render(request, 'news_add.html', {
                'alert_type': 'error',
                'alert_message': f'⚠️ Failed to save: {str(e)}',
                'form_data': request.POST
            })

    # GET request
    return render(request, 'news_add.html')