# officer/forms.py
from django import forms
from schedule.models import Schedule
from announcements.models import Announcement
from depot.models import Depot


class ScheduleForm(forms.ModelForm):
    is_global = forms.BooleanField(
        required=False, 
        label="Apply to all depots",
        help_text="If checked, this schedule will be sent to all depots"
    )
    
    class Meta:
        model = Schedule
        fields = ['title', 'description', 'depot', 'pdf_file', 'is_global']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'depot': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['depot'].queryset = Depot.objects.all().order_by('name')
        self.fields['depot'].required = False
        self.fields['pdf_file'].required = False
        
    def clean(self):
        cleaned_data = super().clean()
        is_global = cleaned_data.get('is_global')
        depot = cleaned_data.get('depot')
        
        if not is_global and not depot:
            raise forms.ValidationError("You must either select a specific depot or check 'Apply to all depots'.")
        
        return cleaned_data


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'priority']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
            'priority': forms.Select(),
        }


class MessageForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message here...'}),
        label="Message"
    )