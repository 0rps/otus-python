from django import forms

from . import models


class SignupForm(forms.Form):

    login = forms.CharField(label='Login',
                            min_length=4,
                            max_length=32,
                            widget=forms.TextInput(attrs={'class': 'form-control',
                                                          'placeholder': 'Login'}))
    password = forms.CharField(label='Password',
                               min_length=6,
                               widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                 'placeholder': 'Password'}))
    re_password = forms.CharField(label='Repeat password',
                                  widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                    'placeholder': 'Repeat password'}))
    email = forms.EmailField(label='Email',
                             widget=forms.EmailInput(attrs={'class': 'form-control',
                                                            'placeholder': 'Email'}))
    avatar = forms.ImageField(label='Avatar image', required=False)

    def clean(self):
        cleaned_data = super().clean()

        if 'password' in cleaned_data and 're_password' in cleaned_data:
            if cleaned_data['password'] != cleaned_data['re_password']:
                msg = 'Passwords are not equal'
                self.add_error('password', msg)
            else:
                del cleaned_data['re_password']

        if 'login' in cleaned_data:
            users = models.User.objects.filter(login__exact=cleaned_data['login'])
            if len(users) > 0:
                self.add_error('login', 'Login is occupied')

        if 'email' in cleaned_data:
            emails = models.User.objects.filter(email__exact=cleaned_data['email'])
            if len(emails) > 0:
                self.add_error('email', 'Email is occupied')

        return cleaned_data


class LoginForm(forms.Form):

    login = forms.CharField(label='Login',
                            min_length=4,
                            max_length=32,
                            widget=forms.TextInput(attrs={'class': 'form-control',
                                                          'placeholder': 'Login'}))
    password = forms.CharField(label='Password',
                               min_length=6,
                               widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                 'placeholder': 'Password'}))


class ProfileForm(forms.Form):

    login = forms.CharField(label='Login', widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True}))

    email = forms.EmailField(label='Email',
                             widget=forms.EmailInput(attrs={'class': 'form-control',
                                                            'placeholder': 'Email'}))
    avatar = forms.ImageField(label='Avatar', required=False)
