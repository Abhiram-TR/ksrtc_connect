from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from accounts.models import User
from depot.models import Depot
from communication.models import Message
from schedule.models import Schedule
from announcements.models import Announcement
from .forms import ScheduleForm, AnnouncementForm, MessageForm
import json
from django.utils import timezone
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def officer_required(view_func):
    """Decorator to check if the user is an officer"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.user_type != 'officer':
            messages.error(request, "You must be logged in as an officer to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@officer_required
def dashboard(request):
    """Officer main dashboard showing all depots"""
    # Get all depots 
    depots = Depot.objects.all().order_by('name')
    
    # Filter active depots (those who have logged in recently)
    active_depots = depots.filter(user__last_login_time__gte=timezone.now() - timezone.timedelta(hours=24))
    
    # Recent announcements
    recent_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Counts for summary
    total_depots = depots.count()
    active_depots_count = active_depots.count()
    unread_messages_count = Message.objects.filter(
        receiver=request.user, 
        is_read=False
    ).count()
    
    context = {
        'depots': depots,
        'active_depots': active_depots,
        'total_depots': total_depots,
        'active_depots_count': active_depots_count,
        'unread_messages_count': unread_messages_count,
        'recent_announcements': recent_announcements,
    }
    
    return render(request, 'officer/dashboard.html', context)


@login_required
@officer_required
def depot_detail(request, depot_id):
    """Depot dashboard showing details about a specific depot"""
    depot = get_object_or_404(Depot, id=depot_id)
    
    # Get messages between officer and this depot
    depot_user = depot.user
    messages_list = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=depot_user)) |
        (Q(sender=depot_user) & Q(receiver=request.user))
    ).order_by('timestamp')
    
    # Get schedules for this depot
    schedules = Schedule.objects.filter(
        Q(depot=depot) | Q(is_global=True)
    ).order_by('-created_at')
    
    # Initialize message form
    message_form = MessageForm()
    
    # Initialize schedule form
    schedule_form = ScheduleForm(initial={'depot': depot})
    
    context = {
        'depot': depot,
        'messages': messages_list,
        'schedules': schedules,
        'message_form': message_form,
        'schedule_form': schedule_form,
    }
    
    # Mark unread messages as read
    if messages_list.exists():
        Message.objects.filter(sender=depot_user, receiver=request.user, is_read=False).update(is_read=True)
    
    return render(request, 'officer/depot_detail.html', context)

@login_required
@officer_required
def announcements(request):
    """List and create announcements"""
    announcements_list = Announcement.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(announcements_list, 10)
    page = request.GET.get('page')
    announcements_paginated = paginator.get_page(page)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            
            # Create message for all depots
            depot_users = User.objects.filter(user_type='depot')
            for depot_user in depot_users:
                Message.objects.create(
                    sender=request.user,
                    receiver=depot_user,
                    content=f"ANNOUNCEMENT: {announcement.title}\n\n{announcement.content}",
                    is_announcement=True
                )
            
            messages.success(request, "Announcement created successfully!")
            return redirect('officer:announcements')
    else:
        form = AnnouncementForm()
    
    context = {
        'announcements': announcements_paginated,
        'form': form,
    }
    
    return render(request, 'officer/announcements.html', context)


@login_required
@officer_required
@require_POST
def send_message(request, depot_id):
    """Send a message to a specific depot"""
    depot = get_object_or_404(Depot, id=depot_id)
    form = MessageForm(request.POST)
    
    if form.is_valid():
        content = form.cleaned_data['content']
        
        # Create the message
        Message.objects.create(
            sender=request.user,
            receiver=depot.user,
            content=content,
            is_read=False,
            is_announcement=False
        )
        
        messages.success(request, "Message sent successfully!")
    else:
        messages.error(request, "Failed to send message. Please check the form.")
    
    return redirect('officer:depot_detail', depot_id=depot_id)


@login_required
@officer_required
@require_POST
def create_schedule(request, depot_id=None):
    """Create a schedule for a specific depot or for all depots"""
    form = ScheduleForm(request.POST, request.FILES)
    
    if form.is_valid():
        schedule = form.save(commit=False)
        schedule.created_by = request.user
        
        # Check if it's for all depots
        if schedule.is_global:
            schedule.depot = None
        
        # Generate PDF if not provided
        if not schedule.pdf_file and schedule.title and schedule.description:
            pdf_buffer = io.BytesIO()
            
            # Create the PDF
            pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Content
            elements = []
            elements.append(Paragraph(f"Schedule: {schedule.title}", styles['Heading1']))
            elements.append(Paragraph(f"Created by: {request.user.get_full_name()}", styles['Normal']))
            elements.append(Paragraph(f"Date: {timezone.now().strftime('%Y-%m-%d')}", styles['Normal']))
            elements.append(Paragraph("", styles['Normal']))  # Spacer
            elements.append(Paragraph(schedule.description, styles['Normal']))
            
            # Build the PDF
            pdf.build(elements)
            
            # Get the value of the BytesIO buffer
            pdf_value = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            # Save the PDF to the model's FileField
            from django.core.files.base import ContentFile
            schedule.pdf_file.save(f"{schedule.title.replace(' ', '_')}.pdf", ContentFile(pdf_value))
        
        schedule.save()
        
        # Create notification message for the depot
        if schedule.depot:
            Message.objects.create(
                sender=request.user,
                receiver=schedule.depot.user,
                content=f"New schedule has been assigned: {schedule.title}",
                is_read=False,
                is_announcement=False
            )
        else:
            # Notify all depots if global
            depot_users = User.objects.filter(user_type='depot')
            for depot_user in depot_users:
                Message.objects.create(
                    sender=request.user,
                    receiver=depot_user,
                    content=f"New global schedule has been assigned: {schedule.title}",
                    is_read=False,
                    is_announcement=False
                )
        
        messages.success(request, "Schedule created successfully!")
        
        # Redirect back to appropriate page
        if depot_id:
            return redirect('officer:depot_detail', depot_id=depot_id)
        else:
            return redirect('officer:dashboard')
    else:
        messages.error(request, "Failed to create schedule. Please check the form.")
        
        if depot_id:
            return redirect('officer:depot_detail', depot_id=depot_id)
        else:
            return redirect('officer:dashboard')


@login_required
@officer_required
def all_messages(request):
    """View all messages for the officer"""
    # Get all depots
    depots = Depot.objects.all()
    
    # Selected depot for filtering
    selected_depot_id = request.GET.get('depot')
    
    # Base query
    messages_query = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-timestamp')
    
    # Apply filtering if depot is selected
    if selected_depot_id:
        try:
            selected_depot = Depot.objects.get(id=selected_depot_id)
            depot_user = selected_depot.user
            messages_query = messages_query.filter(
                Q(sender=depot_user) | Q(receiver=depot_user)
            )
        except Depot.DoesNotExist:
            pass
    
    # Pagination
    paginator = Paginator(messages_query, 20)
    page = request.GET.get('page')
    messages_paginated = paginator.get_page(page)
    
    context = {
        'message_list': messages_paginated,
        'depots': depots,
        'selected_depot_id': selected_depot_id,
    }
    
    return render(request, 'officer/all_messages.html', context)


@login_required
@officer_required
def all_schedules(request):
    """View all schedules"""
    schedules = Schedule.objects.all().order_by('-created_at')
    
    # Filtering
    depot_id = request.GET.get('depot')
    if depot_id:
        try:
            depot = Depot.objects.get(id=depot_id)
            schedules = schedules.filter(Q(depot=depot) | Q(is_global=True))
        except Depot.DoesNotExist:
            pass
    
    # Pagination
    paginator = Paginator(schedules, 10)
    page = request.GET.get('page')
    schedules_paginated = paginator.get_page(page)
    
    # Initialize schedule form
    form = ScheduleForm()
    depots = Depot.objects.all()
    
    context = {
        'schedules': schedules_paginated,
        'form': form,
        'depots': depots,
        'selected_depot_id': depot_id,
    }
    
    return render(request, 'officer/all_schedules.html', context)

def all_depots(request):
    """View for listing all depots"""
    # Get filter parameter from request
    status = request.GET.get('status')
    
    # Base queryset
    depots = Depot.objects.all().order_by('name')
    
    # Apply filtering if provided
    if status == 'active':
        depots = depots.filter(is_active=True)
    elif status == 'inactive':
        depots = depots.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(depots, 12)  # Show 12 depots per page
    page = request.GET.get('page')
    depots = paginator.get_page(page)
    
    context = {
        'depots': depots,
    }
    
    return render(request, 'officer/all_depots.html', context)
# Add these to your views.py file

@login_required
@officer_required
def create_announcement(request):
    """Create a new announcement"""
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            
            # Create message for all depots
            depot_users = User.objects.filter(user_type='depot')
            for depot_user in depot_users:
                Message.objects.create(
                    sender=request.user,
                    receiver=depot_user,
                    content=f"ANNOUNCEMENT: {announcement.title}\n\n{announcement.content}",
                    is_announcement=True
                )
            
            messages.success(request, "Announcement created successfully!")
    
    return redirect('officer:announcements')


@login_required
@officer_required
def update_announcement(request, announcement_id):
    """Update an existing announcement"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "Announcement updated successfully!")
        else:
            messages.error(request, "Failed to update announcement. Please check the form.")
    
    return redirect('officer:announcements')


@login_required
@officer_required
def delete_announcement(request, announcement_id):
    """Delete an announcement"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, "Announcement deleted successfully!")
    
    return redirect('officer:announcements')