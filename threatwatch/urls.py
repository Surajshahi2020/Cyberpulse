from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from collect import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('adding_new/', views.newsfeeding, name='news_feed'),
    path('search_news/', views.newsSearching, name='news_search'),
    path('visualize_news/', views.newsVisualization, name='news_visualization'),
    path('trending_news/', views.newsTrending, name='news_trending'),
    path('report_news/', views.newsReport, name='news_report'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    
