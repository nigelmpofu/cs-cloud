from smtplib import SMTPException
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout
from cloud.decorators.adminRequired import admin_required
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .tokens import tokenizer
from .forms import UserForm
from .mailer import send_password_request_email
from .models import User

@admin_required
def user_admin(request):
	user_form = UserForm()
	context = {'userForm': user_form}
	return render(request, 'cloud/userAdmin.html', context)

@admin_required
def admin_files(request):
	return HttpResponse("Admin Files")


def create_new_user(user_id, user_title, user_initials, user_name, user_surname, user_cell, user_email, user_admin, user_quota):
	random_password = User.objects.make_random_password(8) # Random password 8 characters long
	user = User.objects.create_user(title=user_title, initials=user_initials, name=user_name, surname=user_surname,
									cell=user_cell, email=user_email, user_id=user_id, OTP=True, is_staff=user_admin,
									disk_quota=user_quota, password=random_password)

	if user:
		user_token = tokenizer.make_token(user)
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

			try:
				user = create_new_user(post_user_id, post_title, post_initials, post_name, post_surname, post_cell,
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
				return JsonResponse({'result': 0})
		else:
			# Request error
			return JsonResponse({'result': -1})
	else:
		# Get request not allowed
		return JsonResponse({'result': -1})
