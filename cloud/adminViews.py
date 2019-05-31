import os
import re
from smtplib import SMTPException
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout
from cloud.decorators.adminRequired import admin_required
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .tokens import tokenizer
from .forms import UserForm
from .mailer import send_password_request_email
from .models import User
from .views import reset_password

@admin_required
def user_admin(request):
	user_form = UserForm()
	users = User.objects.all
	context = {'userForm': user_form, 'users': users}
	return render(request, 'cloud/userAdmin.html', context)

@admin_required
def admin_files(request):
	"""
	Create admin user directory if account created with 
		python3 manage.py createsuperuser
	as the user directory might not have been created
	"""
	user_directory = settings.MEDIA_ROOT + "/" + request.user.user_id
	if not os.path.exists(user_directory):
		try:
			os.mkdir(user_directory)
		except OSError:
			messages.error(request, "Error accessing your data.<br/>Contact admin")
			logout(request)
			return redirect("index")
				
	return HttpResponse("Admin Files")


@admin_required
def disk_usage(request):
	return HttpResponse("Disk Usage")


def create_new_user(request, user_id, user_title, user_initials, user_name, user_surname, user_cell, user_email, user_admin, user_quota):
	random_password = User.objects.make_random_password(9) # Random password 9 characters long
	user = User.objects.create_user(title=user_title, initials=user_initials, name=user_name, surname=user_surname,
									cell=user_cell, email=user_email, user_id=user_id, OTP=True, is_staff=user_admin,
									disk_quota=user_quota, password=random_password)

	if user:
		user_directory = settings.MEDIA_ROOT + "/" + user.user_id
		if not os.path.exists(user_directory):
			try:
				os.mkdir(user_directory)
			except OSError:
				# User Directory could not be create
				messages.error(request, "User directory could not be created")
				user.delete()
				return None
		user_token = tokenizer.make_token(user) # Create password reset token
		send_password_request_email(user_token, user_id, user_email, user_name, user_surname, True, random_password)
		user.save()

	return user


@admin_required
def submit_user(request):
	if request.method == 'POST':
		user_form = UserForm(request.POST)
		user_form.full_clean()
		if user_form.is_valid():
			# Form valid			
			post_user_id = user_form.cleaned_data['user_id']
			post_title = user_form.cleaned_data['title']
			post_initials = user_form.cleaned_data['initials']
			post_name = user_form.cleaned_data['name']
			post_surname = user_form.cleaned_data['surname']
			post_cell = user_form.cleaned_data['cell']
			post_email = user_form.cleaned_data['email']
			if user_form.cleaned_data['acc_type'] == "A":
				post_is_admin = True
			else:
				post_is_admin = False
			post_quota = int(user_form.cleaned_data['quota']) * 1024 * 1024 # Convert Mib to bytes

			# Check if username/email available
			if User.objects.filter(user_id=post_user_id).exists():
				messages.error(request, "Error: The username is taken")
				return redirect("userAdmin")

			if User.objects.filter(email=post_email).exists():
				messages.error(request, "Error: The email address is already in use")
				return redirect("userAdmin")

			try:
				user = create_new_user(request, post_user_id, post_title, post_initials, post_name, post_surname, post_cell,
										post_email, post_is_admin, post_quota)
				if not user:
					messages.error(request, "Error: User account could not be created")
				else:
					messages.success(request, "User account created successfully")
			except SMTPException:
				messages.error(request, "Error: Password reset email could not be sent")
		else:
			messages.error(request, "There was a problem processing your form<br/>Please check that it is filled in correctly.")
	else:
		messages.error(request, "There was an error processing your request")
	return redirect("userAdmin")

"""
Check if a given user already exists
"""
@admin_required
def check_user(request):
	if request.method == 'POST':
		"""
		Data to search
		data = 'ui' for user_id
		data = 'em' for email
		everything else is an error

		Return
		0 - Available
		1 - Not Available
		2 - Email not valid
		"""
		search_data = request.POST.get("data", "")
		search_query = request.POST.get("query", None)
		if search_data == "ui":			
			if User.objects.filter(user_id=search_query).exists():
				return JsonResponse({'result': 1})
			else:				
				return JsonResponse({'result': 0})
		elif search_data == "em":
			if User.objects.filter(email=search_query).exists():
				return JsonResponse({'result': 1})
			else:
				# Check if email valid
				if re.match("^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$", search_query) != None:
					return JsonResponse({'result': 0})
				else:
					# Email not valid
					return JsonResponse({'result': 2})
		else:
			# Request error
			return JsonResponse({'result': -1})
	else:
		# Get request not allowed
		return JsonResponse({'result': -1})


def str2bool(v):
	return v.lower() in ("yes", "true", "t", "1")


@admin_required
def edit_user(request):
	if request.method == 'POST':
		post_user_id = request.POST.get("user_id")
		post_title = request.POST.get("title")
		post_initials = request.POST.get("initials")
		post_name = request.POST.get("name")
		post_surname = request.POST.get("surname")
		post_cell = request.POST.get("cell")
		post_email = request.POST.get("email")
		post_quota = request.POST.get("quota")
		post_is_admin = request.POST.get("acc_type")
		user = get_object_or_404(User, pk=post_user_id)

		# Save changes
		user.title = post_title
		user.initials = post_initials
		user.name = post_name
		user.surname = post_surname
		user.cell = post_cell
		user.email = post_email
		user.disk_quota = post_quota
		user.is_staff = str2bool(post_is_admin)		
		user.save()
		return HttpResponse()
	else:
		# Get Request not allowed
		return HttpResponseForbidden()


@admin_required
def admin_reset_password(request):
	if request.method == 'POST':
		user_id = request.POST.get("p_user_id")
		response = reset_password(request, users_id=user_id)
		#messages.success(request, "Password reset email sent")
		return redirect("userAdmin")
	else:
		# Get not allowed
		return HttpResponseForbidden()


@admin_required
def users_delete(request):
	if request.method == 'POST':
		accounts_to_delete = request.POST.getlist("toDelete[]")
		for user_id in accounts_to_delete:
			user = get_object_or_404(User, pk=user_id)
			if user == request.user:
				# Cannot delete yourself
				continue
			user.delete()
		# Deletion complete
		return HttpResponse()
	else:
		# You don't get it
		return HttpResponseForbidden()

