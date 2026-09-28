from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import Address, CustomerProfile, Review

class MobileLoginForm(forms.Form):
    phone = forms.CharField(
        max_length=15,
        label='Mobile number',
        validators=[RegexValidator(r'^\+?[0-9]{10,15}$', 'Enter a valid mobile number.')],
        widget=forms.TextInput(attrs={'inputmode': 'tel', 'autocomplete': 'tel', 'placeholder': '+91 9876543210'}),
    )

    def clean_phone(self):
        return self.cleaned_data['phone'].replace(' ', '').replace('-', '')

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        label='Verification code',
        widget=forms.TextInput(attrs={'inputmode': 'numeric', 'autocomplete': 'one-time-code', 'placeholder': '6-digit OTP'}),
    )
    latitude = forms.CharField(required=False, widget=forms.HiddenInput())
    longitude = forms.CharField(required=False, widget=forms.HiddenInput())

class RegisterForm(UserCreationForm):
    email=forms.EmailField(); first_name=forms.CharField(max_length=30); phone=forms.CharField(max_length=15,required=False)
    class Meta: model=User; fields=('username','first_name','email','phone','password1','password2')
    def save(self,commit=True):
        user=super().save(commit=False); user.email=self.cleaned_data['email']; user.first_name=self.cleaned_data['first_name']
        if commit: user.save(); CustomerProfile.objects.create(user=user,phone=self.cleaned_data['phone'])
        return user
class ProfileForm(forms.ModelForm):
    first_name=forms.CharField(max_length=30); email=forms.EmailField()
    class Meta: model=CustomerProfile; fields=('phone','city','pin_code','budget')
    def __init__(self,*a,**kw): super().__init__(*a,**kw); self.fields['first_name'].initial=self.instance.user.first_name; self.fields['email'].initial=self.instance.user.email
    def save(self,commit=True):
        p=super().save(commit=False); p.user.first_name=self.cleaned_data['first_name']; p.user.email=self.cleaned_data['email']; p.user.save()
        if commit:p.save()
        return p
class AddressForm(forms.ModelForm):
    class Meta: model=Address; fields=('full_name','phone','house','street','area','city','state','pin_code','is_default')
class ReviewForm(forms.ModelForm):
    class Meta: model=Review; fields=('rating','comment'); widgets={'comment':forms.Textarea(attrs={'rows':3})}
