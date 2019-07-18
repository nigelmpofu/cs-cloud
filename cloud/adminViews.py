import os
import re
import json
import shutil
from smtplib import SMTPException
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from cloud.decorators.adminRequired import admin_required
from cloud.decorators.userRequired import user_required
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from .tokens import tokenizer
from .forms import GroupForm, GroupMemberForm, UserForm
from .mailer import send_password_request_email
from .models import Group, User, UserGroup
from .views import reset_password

@admin_required
def user_admin(request):
	if request.user.is_staff:
		user_form = UserForm()
		users = User.objects.all
		context = {'userForm': user_form, 'users': users}
		return render(request, 'cloud/userAdmin.html', context)
	else:
		# Just incase
		return redirect("fileExplorer")


@admin_required
def group_admin(request):
	if request.user.is_staff:
		group_form = GroupForm()
		groups = Group.objects.annotate(num_users=Count('group'))
		context = {'groupForm': group_form, 'groups': groups}
		return render(request, 'cloud/groupAdmin.html', context)
	else:
		# Just incase
		return redirect("fileExplorer")


@admin_required
def new_group(request):
	if request.method == 'POST':
		group_form = GroupForm(request.POST)
		group_form.full_clean()
		if group_form.is_valid():
			# Form valid
			post_name = group_form.cleaned_data['groupname']

			# Check if group available
			if Group.objects.filter(name=post_name).exists():
				messages.error(request, "Error: The group is already taken")
				return redirect("groupAdmin")

			try:
				group = Group.objects.create(name=post_name)
				if not group:
					messages.error(request, "Error: Group could not be created")
				else:
					messages.success(request, "Group created successfully")
			except Exception as ex:
				messages.error(request, "Error: Group could not be created<br/>" + str(ex))
		else:
			messages.error(request, "There was a problem processing your form<br/>Please check that it is filled in correctly.")
	else:
		messages.error(request, "There was an error processing your request")
	return redirect("groupAdmin")


@admin_required
def delete_group(request):
	if request.user.is_staff:
		if request.method == 'POST':
			groups_to_delete = request.POST.getlist("toDelete[]")
			for group_id in groups_to_delete:
				group = get_object_or_404(Group, pk=group_id)
				group.delete()
			# Deletion complete
			return HttpResponse()
		else:
			# You don't get it
			return HttpResponseForbidden()
	else:
		return redirect("fileExplorer")

@admin_required
def list_group(request):
	if request.user.is_staff:
		user_groups = None
		try:
			user_groups = UserGroup.objects.filter(user=User(user_id=request.GET.get("uid")))
		except UserGroup.DoesNotExist:
			user_groups = None
		context = {'members': user_groups}
		return render(request, 'cloud/userGroupFrame.html', context)
	else:
		return redirect("fileExplorer")


@admin_required
def add_group_member(request):
	if request.user.is_staff:
		guser_form = GroupMemberForm(request.POST)
		guser_form.full_clean()
		if guser_form.is_valid():
			new_username = guser_form.cleaned_data['username']
			cur_group_id = guser_form.cleaned_data['gid']
			if not User.objects.filter(user_id=new_username).exists():
				return JsonResponse({'result': 2}) # User not found
			else:
				user = get_object_or_404(User, user_id=new_username)
				group = get_object_or_404(Group, pk=cur_group_id)
				if UserGroup.objects.filter(user=user, group=group).exists():
					return JsonResponse({'result': 1}) # User already in group
				else:
					# Add user to group
					usrgroup = UserGroup.objects.create(user=user, group=group)
					if not usrgroup:
						return JsonResponse({'result': 3}) # Error
					else:
						return JsonResponse({'result': 0}) # Success
		else:
			return JsonResponse({'result': 3}) # Error
	else:
		return JsonResponse({'result': 3}) # Error


@admin_required
def remove_group_member(request):
	if request.user.is_staff:
		if request.method == "POST":
			user_id = request.POST.get("uid", None)
			group_id = request.POST.get("gid", None)
			if user_id is None or group_id is None:
				return HttpResponseForbidden("Request Error")
			else:
				usergroup = get_object_or_404(UserGroup, user=User(user_id=user_id), group=Group(pk=group_id))
				usergroup.delete()
				# Removal complete
				return HttpResponse()
		else:
			return HttpResponseForbidden("Request Error")
	else:
		return HttpResponseForbidden("Request Error")


@admin_required
def list_members(request):
	if request.user.is_staff:
		group_members = None
		try:
			group_members = UserGroup.objects.filter(group=Group(pk=request.GET.get("gid")))
		except UserGroup.DoesNotExist:
			group_members = None
		context = {'members': group_members, 'gmemberForm': GroupMemberForm()}
		return render(request, 'cloud/groupMemberFrame.html', context)
	else:
		return redirect("fileExplorer")

@user_required
def disk_data(request):
	if request.user.is_staff and request.method == 'POST':
		# Sort by used space
		user_disk_info = list(User.objects.extra(select={'name': 'user_id', 'y': 'used_quota'}).values("name", "y").order_by("y"))
		total_used = 0
		for amount in User.objects.values("used_quota"):
			total_used += int(amount["used_quota"])
		user_disk_info.append({'name': "* USED SPACE", 'y': total_used}) # Get free disk space
		user_disk_info.append({'name': "* FREE SPACE", 'y': shutil.disk_usage(settings.MEDIA_ROOT)[2]}) # Get free disk space
		# Highcharts JSON Format - :.2f
		'''
		disk_info = {
			'chart': {'type': 'pie'},
			'title': {'text': 'Disk Usage Information'},
			'subtitle': {'text': 'Disk storage space used by each user'},
			'tooltip': {
				'headerFormat': '<span style="font-size:12px">{series.name}</span><br>',
				'pointFormat': '{point.name}: <b>{point.y} bytes</b><br/>'
				#'pointFormatter': 'function () {return bytesFormat({point.y});}'
			},
			'plotOptions': {
				'pie': {
					'allowPointSelect': 'true',
					'dataLabels': {
						'enabled': 'true',
						'format': '<b>{point.name}</b>: {point.percentage:.1f}%'
					}
				}
			},
			'series': [{
				'name': 'Used',
				'colorByPoint': 'true',
				'data': user_disk_info
			}]
		}
		return JsonResponse(disk_info)
		'''

		json_data = json.dumps(user_disk_info, cls=DjangoJSONEncoder)
		return HttpResponse(json_data, content_type='application/json')
	elif not request.user.is_staff and request.method == 'POST':
		# Normal users
		user_disk_info = list()
		for amount in User.objects.filter(pk=request.user.pk).values("disk_quota", "used_quota"):
			user_disk_info.append({'name': "* USED SPACE", 'y': int(amount["used_quota"])}) # Get used disk space
			if int(amount["disk_quota"]) == 0:
				# Unlimited Disk space limited to disk space
				user_disk_info.append({'name': "* FREE SPACE", 'y': shutil.disk_usage(settings.MEDIA_ROOT)[2]}) # Get free disk space
			else:
				user_disk_info.append({'name': "* FREE SPACE", 'y': int(amount["disk_quota"]) - int(amount["used_quota"])}) # Get free disk space
		json_data = json.dumps(user_disk_info, cls=DjangoJSONEncoder)
		return HttpResponse(json_data, content_type='application/json')
	else:
		# Not an admin
		return HttpResponseForbidden("Access Denied")


@user_required
def disk_usage(request):
	context = {}
	return render(request, 'cloud/diskUsage.html', context)


def create_new_user(request, user_id, user_title, user_initials, user_name, user_surname, user_cell, user_email, user_admin, user_quota):
	random_password = User.objects.make_random_password(9) # Random password 9 characters long
	user = User.objects.create_user(title=user_title, initials=user_initials, name=user_name, surname=user_surname,
									cell=user_cell, email=user_email, user_id=user_id, OTP=True, is_staff=user_admin,
									disk_quota=user_quota, password=random_password)

	if user:
		user_directory = settings.MEDIA_ROOT + "/" + user.user_id
		user_trash = settings.TRASH_ROOT + "/" + user.user_id
		if not os.path.exists(user_directory):
			try:
				os.mkdir(user_directory)
			except OSError:
				# User Directory could not be create
				messages.error(request, "User directory could not be created")
				user.delete()
				return None
		if not os.path.exists(user_trash):
			try:
				os.mkdir(user_trash)
			except OSError:
				# User Directory could not be create
				messages.error(request, "User trash directory could not be created")
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


"""
Check if a given group already exists
"""
@admin_required
def check_group(request):
	if request.method == 'POST':
		"""
		Data to search
		data = 'gn' for group name
		everything else is an error

		Return
		0 - Available
		1 - Not Available
		"""
		search_data = request.POST.get("data", "")
		search_query = request.POST.get("query", None)
		if search_data == "gn":
			if Group.objects.filter(name=search_query).exists():
				return JsonResponse({'result': 1})
			else:
				return JsonResponse({'result': 0})
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
		user.is_superuser = str2bool(post_is_admin)
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
			user_directory = settings.MEDIA_ROOT + "/" + user.user_id
			user_trash = settings.TRASH_ROOT + "/" + user.user_id
			try:
				# Possible Improvements: Better error handling and reporting
				shutil.rmtree(user_directory, ignore_errors=True) # Delete ALL user data
				shutil.rmtree(user_trash, ignore_errors=True) # Delete ALL user trash
			except Exception as ex:
				pass
			user.delete()
		# Deletion complete
		return HttpResponse()
	else:
		# You don't get it
		return HttpResponseForbidden()

