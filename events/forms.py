from django import forms
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import Owner, Profile
from .models import Inventory, Booking


phone_validator = RegexValidator(
    regex=r'^\d{10}$',
    message="Enter a valid 10-digit phone number"
)

class CustomerSignupForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    phone = forms.CharField(validators=[phone_validator])

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('password') != cleaned_data.get('confirm_password'):
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data
    
def clean_email(self):
    email = self.cleaned_data.get('email')

    if User.objects.filter(username=email).exists():
        raise forms.ValidationError("Email already registered")

    return email

class OwnerSignupForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    phone = forms.CharField(validators=[phone_validator])
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    company_name = forms.CharField()
    service_type = forms.ChoiceField(choices=Owner.SERVICE_CHOICES)
    location = forms.CharField()
    state = forms.CharField()
    district = forms.CharField()
    license_id = forms.CharField()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match")
        return cleaned
    


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['name', 'category', 'subcategory', 'sub_type', 'quantity', 'price_per_day', 'description', 'images']

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['quantity', 'start_date', 'end_date', 'district', 'venue', 'needs_transportation', 'needs_setup']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class OwnerUpdateForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = ['company_name', 'phone', 'location', 'district', 'state']