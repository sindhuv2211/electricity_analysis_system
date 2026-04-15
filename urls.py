# app/urls.py - URL routing for all views

from django.urls import path
from . import views

urlpatterns = [
    path('',           views.login_view,     name='login'),
    path('signup/',    views.signup_view,    name='signup'),
    path('logout/',    views.logout_view,    name='logout'),
    path('dashboard/', views.dashboard,      name='dashboard'),
    path('analytics/', views.analytics,      name='analytics'),
    path('admin-panel/',  views.admin_panel, name='admin_panel'),
    path('upload/',    views.upload_csv,     name='upload'),
    path('add-data/',  views.add_data,       name='add_data'),
    path('edit-data/<str:record_id>/', views.edit_data, name='edit_data'),
    path('delete-data/<str:record_id>/', views.delete_data, name='delete_data'),
    path('export-csv/', views.export_csv,   name='export_csv'),
]
