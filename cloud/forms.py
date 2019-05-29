from django import forms
from django.contrib.auth.forms import SetPasswordForm

from cloud.models import User

class LoginForm(forms.Form):
	username = forms.Field(widget=forms.TextInput(attrs={'class': 'form-control',
														'placeholder': 'Username',
														'required': True, 'autofocus': True}))
	password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control',
																'placeholder': 'Password', 'required': True}))


class RecoverPasswordForm(SetPasswordForm):
	def __init__(self, user, url_token, *args, **kwargs):
		super(RecoverPasswordForm, self).__init__(user, *args, **kwargs)

		# Adds a hidden char field containing the token
		self.fields['urlToken'] = forms.CharField(widget=forms.HiddenInput(), required=False)
		self.initial['urlToken'] = url_token
		self.fields['userID'] = forms.CharField(widget=forms.HiddenInput(), required=False)
		if not user.is_anonymous:
			self.initial['userID'] = user.user_id
		self.fields['new_password1'] = forms.CharField(label="New Password", 
													widget=forms.PasswordInput(attrs={'class': 'form-control',
													'placeholder': 'New Password', 'required': True, 'autofocus': True}))
		self.fields['new_password2'] = forms.CharField(label="Confirm Password", 
													widget=forms.PasswordInput(attrs={'class': 'form-control',
													'placeholder': 'New Password', 'required': True}))

	def save(self, commit=True):
		self.save()


class ResetForm(forms.Form):
	class Meta:
		model = User
		fields = ['user_id']
	
	user_id = forms.CharField(
		label="Username:",
		max_length=16,
		widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'user_id', 'required': True, 'autofocus': True}))

