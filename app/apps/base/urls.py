from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('card.png', views.site_card, name='site_card'),
    path('partners/', views.partners, name='site_partners'),
    path('partners/<slug:slug>/', views.partner_detail, name='site_partner'),
    path('partners/<slug:slug>/og.png', views.partner_og, name='site_partner_og'),
    path('partners/<slug:slug>/card.png', views.partner_card, name='site_partner_card'),
]
