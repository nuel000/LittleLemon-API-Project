"""
URL configuration for LittleLemon project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path,include,re_path
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from rest_framework.routers import DefaultRouter
from djoser.views import UserViewSet


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('LittleLemonAPI.urls')),
    path('api/', include('djoser.urls')),
    path('api/users/', include('djoser.urls')),# for displaying the current user with token use the "/api/users/users/me/" endpoint
    path('', include('djoser.urls.authtoken')), # for token generation with valid username and password
    ]