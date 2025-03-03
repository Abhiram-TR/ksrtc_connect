from rest_framework import serializers
from depot.models import Depot
from accounts.models import User
from communication.models import Message
from schedule.models import Schedule
from announcements.models import Announcement


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'user_type', 'last_login_time']


class DepotSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Depot
        fields = ['id', 'user', 'name', 'location', 'address', 'contact_person', 'is_active', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    receiver_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'sender_name', 'receiver_name', 'content', 'timestamp', 'is_read', 'is_announcement']
    
    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.username
    
    def get_receiver_name(self, obj):
        if obj.receiver:
            return obj.receiver.get_full_name() or obj.receiver.username
        return "All Depots" if obj.is_announcement else None


class ScheduleSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    depot_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Schedule
        fields = ['id', 'title', 'description', 'created_by', 'created_by_name', 'depot', 'depot_name', 'pdf_file', 'created_at', 'is_global']
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username
    
    def get_depot_name(self, obj):
        if obj.depot:
            return obj.depot.name
        return "All Depots" if obj.is_global else None


class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'content', 'created_by', 'created_by_name', 'created_at', 'priority', 'is_active']
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username