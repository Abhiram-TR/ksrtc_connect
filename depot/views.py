from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from depot.models import Depot
from communication.models import Message
from schedule.models import Schedule
from announcements.models import Announcement
from .serializers import (
    DepotSerializer, MessageSerializer, 
    ScheduleSerializer, AnnouncementSerializer,UserSerializer
)
from django.utils import timezone
from accounts.models import User
from django.db.models import Q


class IsDepotUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'depot'


class DepotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Depot.objects.all()
    serializer_class = DepotSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            depot = Depot.objects.get(user=request.user)
            serializer = self.get_serializer(depot)
            return Response(serializer.data)
        except Depot.DoesNotExist:
            return Response({"detail": "Depot not found"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def update_login(self, request):
        user = request.user
        user.last_login_time = timezone.now()
        user.save(update_fields=['last_login_time'])
        return Response({"detail": "Login time updated successfully"})

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            # If user is not authenticated, return an empty queryset.
            return Message.objects.none()
        
        # Filter messages for the current user and order them by timestamp descending.
        queryset = Message.objects.filter(receiver=user).order_by('-timestamp')
        return queryset

    @action(detail=False, methods=['get'])
    def unread(self, request):
        queryset = self.get_queryset().filter(is_read=False)
        # If no unread messages exist, return an empty list.
        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        try:
            message = self.get_object()
        except Exception as e:
            return Response({"detail": "Message not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if message is already read.
        if message.is_read:
            return Response({"status": "message already marked as read"}, status=status.HTTP_200_OK)
        
        message.is_read = True
        message.save()
        return Response({"status": "message marked as read"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def send_to_officer(self, request):
        content = request.data.get('content')
        if not content:
            return Response(
                {"detail": "Message content is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Find an officer to send the message to.
            officer_user = User.objects.filter(user_type='officer').first()
            if not officer_user:
                return Response(
                    {"detail": "No officer found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            message = Message.objects.create(
                sender=request.user,
                receiver=officer_user,
                content=content,
                is_read=False,
                is_announcement=False
            )
            
            serializer = self.get_serializer(message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    @action(detail=False, methods=['get'], url_path='conversation/(?P<receiver_id>\d+)')
    def conversation(self, request, receiver_id=None):
        user_id = request.user.id

        # Validate receiver existence.
        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Receiver not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get conversation between the current user and the receiver.
        messages = Message.objects.filter(
            (Q(sender=user_id) & Q(receiver=receiver_id)) | 
            (Q(sender=receiver_id) & Q(receiver=user_id))
        ).order_by('timestamp')
        
        if not messages.exists():
            return Response(
                {"detail": "No conversation found"},
                status=status.HTTP_200_OK
            )
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

class ScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated, IsDepotUser]
    
    def get_queryset(self):
        user = self.request.user
        try:
            depot = Depot.objects.get(user=user)
            # Get schedules specific to this depot or global schedules
            return Schedule.objects.filter(depot=depot) | Schedule.objects.filter(is_global=True)
        except Depot.DoesNotExist:
            return Schedule.objects.none()


class AnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Announcement.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]

class OfficerViewSet(viewsets.ModelViewSet):
    # Define your serializer, queryset, and permissions
    serializer_class = UserSerializer  # Create this if you don't have one
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.filter(user_type='officer')
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        # Get an available officer - modify this logic as needed for your app
        officer = User.objects.filter(user_type='officer').first()
        
        if not officer:
            return Response({"detail": "No officer available"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(officer)
        return Response(serializer.data)