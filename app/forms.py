from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Product

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    numero_cni=forms.CharField(required=True)

    class Meta:
        model = User
        fields = ['role', 'username', 'email', 'phone', 'numero_cni', 'password1', 'password2']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image']

class ProductUpdateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image']

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
            'placeholder': 'Votre nom'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
            'placeholder': 'Votre email'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
            'placeholder': 'Sujet de votre message'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
            'placeholder': 'Votre message',
            'rows': 6
        })
    )