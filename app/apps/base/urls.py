from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('partners/', views.partners, name='site_partners'),
    path('partners/<slug:slug>/', views.partner_detail, name='site_partner'),
]
