from django.urls import path

from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('add/', views.ProjectCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='edit'),
    path('<int:pk>/status/', views.ProjectStatusView.as_view(), name='status'),
    path('<int:pk>/technical/', views.TechnicalInfoView.as_view(), name='technical'),
    path('<int:pk>/members/add/', views.MemberAddView.as_view(), name='member_add'),
    path('<int:pk>/members/<int:member_pk>/remove/', views.MemberRemoveView.as_view(), name='member_remove'),
]
