from django import forms
from django.contrib.auth.forms import SetPasswordForm

from cloud.models import User

class LoginForm(forms.Form):
    userName = forms.Field()
    password = forms.CharField(widget=forms.PasswordInput)
    

class RecoverPasswordForm(SetPasswordForm):
    def __init__(self, user, url_token, *args, **kwargs):
        print(url_token)
        super(RecoverPasswordForm, self).__init__(user, *args, **kwargs)

        # Adds a hidden char field containing the token
        self.fields['urlTokenField'] = forms.CharField(widget=forms.HiddenInput(),
                                                       required=False)
        self.initial['urlTokenField'] = url_token

    def save(self, commit=True):
        self.save()
