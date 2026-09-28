"""Два раздела Hub поверх одной модели Company.

Подключаются в core/urls.py:
    /hub/candidates/ → namespace 'candidates' (карточка и все действия с компанией)
    /hub/partners/   → namespace 'partners'   (список и карточка партнёров)
"""
from django.urls import path

from . import views

candidate_patterns = ([
    path('', views.CandidateListView.as_view(), name='list'),
    path('add/', views.CompanyCreateView.as_view(), name='create'),
    path('<int:pk>/', views.CompanyDetailView.as_view(module='candidates'), name='detail'),
    path('<int:pk>/edit/', views.CompanyUpdateView.as_view(), name='edit'),
    path('<int:pk>/status/', views.StatusChangeView.as_view(), name='status'),
    path('<int:pk>/decision/', views.DecisionCreateView.as_view(), name='decision'),
    path('<int:pk>/make-partner/', views.MakePartnerView.as_view(), name='make_partner'),
    path('<int:pk>/assessment/', views.AssessmentUpdateView.as_view(), name='assessment'),
    path('<int:pk>/contacts/add/', views.ContactCreateView.as_view(), name='contact_add'),
    path('<int:pk>/contacts/<int:contact_pk>/edit/', views.ContactUpdateView.as_view(),
         name='contact_edit'),
    path('<int:pk>/contacts/<int:contact_pk>/delete/', views.ContactDeleteView.as_view(),
         name='contact_delete'),
], 'candidates')

partner_patterns = ([
    path('', views.PartnerListView.as_view(), name='list'),
    path('<int:pk>/', views.CompanyDetailView.as_view(module='partners'), name='detail'),
], 'partners')
