from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class ClientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, help_text="How should we address you?")
    last_name = forms.CharField(max_length=50, required=False)
    email = forms.EmailField(required=True, help_text="We will send session confirmations here.")
    phone_number = forms.CharField(max_length=20, required=False, help_text="Optional for text reminders.")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'username']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CLIENT
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data.get('last_name', '')
        user.phone_number = self.cleaned_data.get('phone_number', '')
        if commit:
            user.save()
        return user
