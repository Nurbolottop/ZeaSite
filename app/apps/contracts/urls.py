from django.urls import path

from . import views

app_name = 'contracts'

urlpatterns = [
    path('', views.ContractListView.as_view(), name='list'),
    path('add/', views.ContractCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ContractDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ContractUpdateView.as_view(), name='edit'),
    path('<int:pk>/status/', views.ContractStatusView.as_view(), name='status'),
    path('<int:pk>/file/', views.ContractFileUploadView.as_view(), name='file_upload'),
    path('<int:pk>/file/download/', views.ContractFileDownloadView.as_view(), name='file_download'),
    path('<int:pk>/documents/add/', views.ContractDocumentCreateView.as_view(), name='document_add'),
    # UUID вместо id — документ не подбирается перебором
    path('documents/<uuid:uid>/download/', views.ContractDocumentDownloadView.as_view(),
         name='document_download'),
]
