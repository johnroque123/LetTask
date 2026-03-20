from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('',        TemplateView.as_view(template_name='landing/home.html'),  name='home'),
    path('about/',  TemplateView.as_view(template_name='landing/about.html'), name='about'),
    path('admin/',        admin.site.urls),
    path('registration/', include('registration.urls')),
    path('todo/',         include('todo.urls')),
    path('notes/',        include('notes.urls')),
    path('habits/',       include('habits.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)