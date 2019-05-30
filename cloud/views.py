from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout
from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from .tokens import tokenizer
from .forms import LoginForm
from .forms import RecoverPasswordForm
from .forms import ResetForm
from .mailer import send_password_request_email
from .models import User

def login(request):
	logout(request)
	login_form = LoginForm()
	context = {'loginForm': login_form}
	return render(request, 'cloud/login.html', context)


def index(request):
	if request.user.is_authenticated:
		if request.user.is_user_admin:
			return redirect('userAdmin')
		else:
			return redirect('files')
	else:
		return login(request)


def auth(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():			
			user_id = form.cleaned_data['username']
			password = form.cleaned_data['password']
			user = authenticate(user_id=user_id, password=password)
			if user:
				if user.is_active:
					# Login
					django_login(request, user)
					# Redirect if OTP is set
					if User.objects.get(user_id=user_id).OTP:
						request.user = user
						return change_password(request)

					# Redirect based on user account type
					if user.is_user_admin:
						return redirect('userAdmin')
					else:
						return redirect('files')
		# Access Denied
		messages.add_message(request, messages.ERROR, "Access Denied")
		return redirect('/')
	else:
		return redirect('/')

def auth_logout(request):
	logout(request)
	return redirect('/')

def recover_password(request):
	if request.method == 'POST':
		reset_form = RecoverPasswordForm(request.user, None, request.POST)
		reset_form.full_clean()
		url_token = reset_form.cleaned_data['urlToken']
		user_id = reset_form.cleaned_data['userID']
		for err, description in reset_form.errors.items():
			messages.error(request, description)

		# Change password if the form is valid
		if reset_form.is_valid():
			try:
				user = User.objects.get(user_id=user_id)
				if not tokenizer.check_token(user, url_token):
					# Invalid token
					messages.error(request, "Your token is invalid.<br/>Please generate a new one.")
					return redirect("forgotPassword")
				else:
					# Valid token
					user.set_password(reset_form.cleaned_data['new_password1'])
					user.OTP = False
					user.save()
					messages.success(request, "Password changed successfully")
					return redirect("login")
			except User.DoesNotExist:
				messages.error(request, "Invalid username, please contact admin if problem persists.")
				return redirect("login")
		else:
			# Error, take back to password change page
			return change_password(request, url_token, user_id)
	else:
		# Not supposed to be get request
		messages.error(request, "The was a problem processing your request.")
		return redirect("login")


def forgot_password(request):
	context = {}
	form = ResetForm()
	context['resetForm'] = form
	return render(request, 'cloud/forgotPassword.html', context)


def reset_password(request):
	if request.method == 'POST':
		reset_form = ResetForm(request.POST)
		reset_form.full_clean()
		user_id = reset_form.cleaned_data['user_id']
		try:
			user = User.objects.get(user_id=user_id)
			user_token = tokenizer.make_token(user)
			mail_success = send_password_request_email(user_token, user.user_id, user.email, user.name, user.surname, False)
			if mail_success:
				messages.success(request, "Check your inbox for a password reset email")
				return redirect("login")
			else:
				messages.error(request, "Could not send password reset email.<br/>Contact admin if problem persists")
				# Try again
				return redirect("forgotPassword")

		except User.DoesNotExist:
			# Probably a bad idea, allows bruteforce username guessing
			messages.error(request, "Error: Username not found")
			return redirect("forgotPassword")		
	else:
		# Get request not allowed
		messages.error(request, "Error: Invalid Request")
		return redirect("forgotPassword")


def reset_password_token(request, user_id, token):
	try:
		user = User.objects.get(user_id=user_id)
		if not tokenizer.check_token(user, token):
			# Invalid token
			messages.error(request, "Your token is invalid.<br/>Please generate a new one.")
			return redirect("login")
		else:
			# Valid token
			#request.user = user			
			return change_password(request, token, user_id)

	except User.DoesNotExist:
		messages.error(request, "Your token is invalid.<br/>Please generate a new one.")
		return redirect("login")


def change_password(request, token=None, users_id=None):
	if token == None:
		user_token = tokenizer.make_token(request.user)
		user_id = request.user.user_id
	else:
		user_token = token
		user_id = users_id
	context = {}

	try:
		user = User.objects.get(user_id=user_id)
		context['username'] = user.user_id

	except Exception as e:
		print(e)

	form = RecoverPasswordForm(user=user, url_token=user_token)
	context['resetForm'] = form
	return render(request, 'cloud/passwordChange.html', context)
