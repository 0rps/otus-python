from django import forms

from . import models


class SignupForm(forms.Form):

    login = forms.CharField(label='Login: ', min_length=4, max_length=32)
    password = forms.CharField(label='Password', min_length=6, widget=forms.PasswordInput)
    re_password = forms.CharField(label='Repeat password', widget=forms.PasswordInput)
    email = forms.EmailField(label='Email')
    avatar = forms.ImageField(label='Avatar image')

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data['password'] != cleaned_data['re_password']:
            msg = 'Passwords are not equal'
            self.add_error('password', msg)
            self.add_error('re_password', msg)

        users = models.User.objects.filter(login__eq=cleaned_data['login'])
        if len(users) > 0:
            self.add_error('login', 'Login is occupied')

        emails = models.User.objects.filter(email__eq=cleaned_data['email'])
        if len(emails) > 0:
            self.add_error('email', 'Email is occupied')

        return cleaned_data
