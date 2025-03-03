"""from django.urls import path
from . import views

app_name = 'officer'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('depots/', views.all_depots, name='all_depots'),
    path('depot/<int:depot_id>/', views.depot_detail, name='depot_detail'),
    path('depot/<int:depot_id>/send-message/', views.send_message, name='send_message'),
    path('depot/<int:depot_id>/create-schedule/', views.create_schedule, name='create_schedule'),
    path('announcements/', views.announcements, name='announcements'),
    path('messages/', views.all_messages, name='all_messages'),
    path('schedules/', views.all_schedules, name='all_schedules'),
    path('schedules/create/', views.create_schedule, name='create_schedule'),
]
"""

from django.urls import path
from . import views

app_name = 'officer'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    # You need to add this line:
    path('depots/', views.all_depots, name='all_depots'),
    # Add other URL patterns...
    path('depot/<int:depot_id>/', views.depot_detail, name='depot_detail'),
    path('messages/', views.all_messages, name='all_messages'),
    path('schedules/', views.all_schedules, name='all_schedules'),
    path('announcements/', views.announcements, name='announcements'),
    path('depot/<int:depot_id>/send-message/', views.send_message, name='send_message'),
    path('depot/<int:depot_id>/create-schedule/', views.create_schedule, name='create_schedule'),
    path('create-schedule/', views.create_schedule, name='create_schedule'),
    path('create-announcement/', views.create_announcement, name='create_announcement'),
    path('announcement/<int:announcement_id>/update/', views.update_announcement, name='update_announcement'),
    path('announcement/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),
]