"""
URL configuration for aero_miles project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views
from django.urls import path, include
from django.urls import path, include 
from accounts import views

urlpatterns = [
    path('', views.register_view, name='home_register'),
    path('admin/', admin.site.urls),
    path('', accounts_views.landing_page, name='home'),
    path('', include('accounts.urls')),
    path('staff/', include('staff.urls')),
    path('member/', include('member.urls')),
    path('accounts/', include('accounts.urls')),
    path('member/', include('member.urls'))
]
