from django import forms
from django.contrib.auth.forms import SetPasswordForm

from cloud.models import User, UserData

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


class UserForm(forms.ModelForm):
	class Meta:
		model = User
		fields = ['user_id', 'acc_type', 'title', 'initials', 'name', 'surname', 'cell', 'email', 'quota']

	user_id = forms.CharField(
		label="Username:",
		max_length=30,
		widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'user_id', 'placeholder': 'Username', 'required': True,
							'onchange': 'checkUser()', 'oninput': 'resetUser()'}))

	acc_type = forms.ChoiceField(
		label="Account Type:",
		choices=(('U', 'User',), ('A', 'Admin',)),
		widget=forms.Select(attrs={'class': 'form-control', 'id': 'acc_type', 'required': True}))

	title = forms.ChoiceField(
		label="Title:",
		choices=(('', '',), ('Mr', 'Mr',), ('Ms', 'Ms',), ('Miss', 'Miss',), ('Mrs', 'Mrs',), ('Dr', 'Dr',)),
		widget=forms.Select(attrs={'class': 'form-control', 'id': 'title'}))

	initials = forms.CharField(
		label="Initials:",
		max_length=5,
		widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'initials', 'placeholder': 'Initials'}))

	name = forms.CharField(
		label="First Name:",
		max_length=50,
		widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'name', 'placeholder': 'First Name'}))

	surname = forms.CharField(
		label="Surname:",
		max_length=50,
		widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'surname', 'placeholder': 'Surname'}))

	cell = forms.CharField(
		label="Cell Number:",
		max_length=10,
		widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'cell', 'placeholder': 'Cellphone Number'}))

	email = forms.EmailField(
		label="Email:",
		max_length=100,
		widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'email', 'placeholder': 'Email Address', 'required': True,
							'onchange': 'checkEmail()', 'oninput': 'resetEmail()'}))

	quota = forms.CharField(
		label="Disk Quota (MB):",
		max_length = 8,
		widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'quota', 'value': 100, 'required': True})) # Default 100 MB


class UploadForm(forms.ModelForm):
	class Meta:
		model = UserData
		fields = ['user_files', 'upload_path']

	user_files = forms.FileField(label='Select files to upload:', widget=forms.ClearableFileInput(attrs={'multiple': True}))
	upload_path = forms.CharField(widget=forms.HiddenInput(), required=True)


class MkdirForm(forms.Form):
	dir_name = forms.CharField(
		label="Directory Name",
		max_length = 16,
		widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'dir_name', 'placeholder': 'Directory Name', 'autocomplete': 'off'}))
	dir_path = forms.CharField(widget=forms.HiddenInput(), required=True)
