from django.urls import path

from . import views

urlpatterns = [
    path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    path('datasets/', views.dataset_list_view, name='dataset_list'),
]