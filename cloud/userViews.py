import os
import uuid
import json
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from cloud.decorators.userRequired import user_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string
from .tokens import tokenizer
from .forms import LoginForm, MkdirForm, RecoverPasswordForm, RenameForm, ResetForm, UploadForm, GroupShareForm, UserShareForm
from .mailer import send_password_request_email, send_share_email
from .models import Group, GroupShare, ShareUrl, User, UserGroup, UserShare
from .fileManager import FileManager

@user_required
def file_explorer(request):
	"""
	Create user directory if account created with 
		python3 manage.py createsuperuser
	as the user directory might not have been created
	"""
	user_directory = settings.MEDIA_ROOT + "/" + request.user.user_id
	user_trash = settings.TRASH_ROOT + "/" + request.user.user_id
	if not os.path.exists(user_directory):
		try:
			os.mkdir(user_directory)
		except OSError:
			messages.error(request, "Error accessing your data.<br/>Contact admin")
			logout(request)
			return redirect("index")
	if not os.path.exists(user_trash):
		try:
			os.mkdir(user_trash)
		except OSError:
			messages.error(request, "Error accessing your data.<br/>Contact admin")
			logout(request)
			return redirect("index")
	fm = FileManager(request.user)
	mkdir_form = MkdirForm()
	rename_form = RenameForm()
	upload_form = UploadForm()
	usershare_from = UserShareForm()
	groupshare_form = GroupShareForm()
	if 'p' in dict(request.GET) and len(dict(request.GET)['p'][0]) > 0:
		new_path = dict(request.GET)['p'][0].replace("../", "") # No previous directory browsing
		fm.update_path(new_path)
		mkdir_form.initial['dir_path'] = new_path
		upload_form.initial['upload_path'] = new_path
	context = {'files': fm.directory_list(), 'uploadForm': upload_form, 'mkdirForm': mkdir_form, 'renameForm': rename_form,
				'usershareForm': usershare_from, 'groupshareForm': groupshare_form}
	fm.update_context_data(context)
	return render(request, 'cloud/fileManager.html', context)


@user_required
def file_move(request):
	fm = FileManager(request.user)
	if request.method == 'GET':
		# Send directory information
		mkdir_form = MkdirForm()
		if 'p' in dict(request.GET) and len(dict(request.GET)['p'][0]) > 0:
			new_path = dict(request.GET)['p'][0].replace("../", "") # No previous directory browsing
			fm.update_path(new_path)
			mkdir_form.initial['dir_path'] = new_path
		context = {'dirs': fm.directory_list(False), 'mkdirForm': mkdir_form}
		fm.update_context_data(context)
		return render(request, 'cloud/moveExplorer.html', context)
	elif request.method == 'POST':
		# Move file to new destination
		cur_path = request.POST.get("fp", None)
		move_path = request.POST.get("np", None)
		if cur_path == None or move_path == None:
			return JsonResponse({'result': 2, 'message': 'Request Error'})
		else:
			return fm.move(cur_path.replace("../", ""), move_path.replace("../", ""))
	else:
		return HttpResponseNotFound("Unknown Request")


@user_required
def trash_explorer(request):
	user_directory = settings.MEDIA_ROOT + "/" + request.user.user_id
	user_trash = settings.TRASH_ROOT + "/" + request.user.user_id
	if not os.path.exists(user_directory):
		try:
			os.mkdir(user_directory)
		except OSError:
			messages.error(request, "Error accessing your data.<br/>Contact admin")
			logout(request)
			return redirect("index")
	if not os.path.exists(user_trash):
		try:
			os.mkdir(user_trash)
		except OSError:
			messages.error(request, "Error accessing your data.<br/>Contact admin")
			logout(request)
			return redirect("index")
	fm = FileManager(request.user)
	context = {'files': fm.trash_list()}
	return render(request, 'cloud/trashManager.html', context)


def file_browser(request):
	# Todo: file handling, sharing and security
	return HttpResponse("File: " + request.GET.get("f"))


def file_delete(request):
	if request.method == 'POST':
		file_path = request.POST.get("fp", None)
		if file_path == None:
			return HttpResponseNotFound("Missing file")
		else:
			file_path = file_path.replace("../", "") # No previous directory browsing
			fm = FileManager(request.user)
			return fm.delete_item(file_path)
	else:
		# Get not allowed
		return HttpResponseForbidden("Not allowed")


def file_delete_perm(request):
	if request.method == 'POST':
		file_path = request.POST.get("fp", None)
		if file_path == None:
			return HttpResponseNotFound("Missing file")
		else:
			file_path = file_path.replace("../", "") # No previous directory browsing
			fm = FileManager(request.user)
			return fm.purge_item(file_path)
	else:
		# Get not allowed
		return HttpResponseForbidden("Not allowed")

def file_restore(request):
	if request.method == 'POST':
		file_path = request.POST.get("fp", None)
		if file_path == None:
			return HttpResponseNotFound("Missing file")
		else:
			file_path = file_path.replace("../", "") # No previous directory browsing
			fm = FileManager(request.user)
			return fm.restore_item(file_path)
	else:
		# Get not allowed
		return HttpResponseForbidden("Not allowed")	


def empty_trash(request):
	if request.method == 'POST':
		fm = FileManager(request.user)
		return fm.empty_trash()
	else:
		# Get not allowed
		return HttpResponseForbidden("Not allowed")


def file_details(request):
	if request.method == 'POST':
		user_rec = None
		file_share = request.POST.get("fs")
		if file_share == "":
			user_rec = request.user
		else:
			if not ShareUrl.objects.filter(url=file_share).exists():
				return HttpResponseNotFound("Missing file")
			else:
				share_data = get_object_or_404(ShareUrl, url=file_share)
				user_rec = share_data.owner
		fm = FileManager(user_rec)
		file_information = {}
		file_path = request.POST.get("filepath", None)
		if file_path == None:
			return HttpResponseNotFound("Missing file")
		else:
			file_path = file_path.replace("../", "") # No previous directory browsing
			file_information = fm.file_details(file_path)
			if bool(file_information): # Not empty
				return JsonResponse(file_information)
			else:
				return HttpResponseNotFound("Missing file")
	else:
		# Reject get request
		return HttpResponseForbidden("Not allowed")


def file_rename(request):
	if request.method == 'POST':
		rename_form = RenameForm(request.POST)
		rename_form.full_clean()
		if rename_form.is_valid():
			fm = FileManager(request.user)
			if fm.rename(rename_form.cleaned_data['rename_path'].replace("../", ""), rename_form.cleaned_data['new_name'].replace("../", "")):
				return JsonResponse({'result': 0})
			else:
				return JsonResponse({'result': 1})
	else:
		# Reject get request
		return HttpResponseForbidden("Not allowed")


def file_download(request):
	file_share = request.GET.get("fs", None)
	if file_share == None:
		fm = FileManager(request.user)
		return fm.download_file(request.GET.get("file"))
	else:
		if not ShareUrl.objects.filter(url=file_share).exists():
			return render(request, 'cloud/e404.html') # 404
		else:
			share_data = get_object_or_404(ShareUrl, url=file_share)
			fm = FileManager(share_data.owner)
			is_file = fm.set_share_path(share_data.path)
			if is_file == 1:
				# Download file
				return fm.download_file(share_data.path)
			else:
				# Download file from shared directory
				return fm.download_file(request.GET.get("file"))


def check_quota(request):
	file_share = request.POST.get("fs")
	if file_share == "":
		return JsonResponse({'available': request.user.get_remaining_quota()})
	else:
		if not ShareUrl.objects.filter(url=file_share).exists():
			return JsonResponse({'available': -1}) # 404
		else:
			share_data = get_object_or_404(ShareUrl, url=file_share)
			return JsonResponse({'available': share_data.owner.get_remaining_quota()})


def file_upload(request):
	if request.method == 'POST':
		upload_form = UploadForm(request.POST, request.FILES)
		upload_form.full_clean()
		user_files = request.FILES.getlist('user_files')
		if upload_form.is_valid():
			file_share = upload_form.cleaned_data['share_url']			
			user_rec = None
			if file_share == "":
				user_rec = request.user
			else:
				if not ShareUrl.objects.filter(url=file_share).exists():
					return JsonResponse({'result': 1})
				else:
					share_data = get_object_or_404(ShareUrl, url=file_share)
					user_rec = share_data.owner
			fm = FileManager(user_rec)
			fm.update_path(upload_form.cleaned_data['upload_path'])
			user_db = get_object_or_404(User, pk=user_rec.user_id)
			insufficient_count = 0
			for file_to_upload in user_files:
				user_db = get_object_or_404(User, pk=user_rec.user_id)
				if file_to_upload.size <= user_db.get_remaining_quota():
					fm.upload_file(file_to_upload)
				else:
					# Not enough space to upload file
					insufficient_count = insufficient_count + 1
			# messages.success(request, "Files uploaded successfully")
			return JsonResponse({'result': 0, 'insufficient': insufficient_count})
		else:
			# messages.error(request, "Files could not be uploaded")
			return JsonResponse({'result': 1})
	else:
		# No get allowed
		return HttpResponseForbidden("Upload Rejected")


def create_directory(request):
	if request.method == 'POST':
		mkdir_form = MkdirForm(request.POST)
		mkdir_form.full_clean()
		if mkdir_form.is_valid():
			file_share = mkdir_form.cleaned_data['share_url']			
			user_rec = None
			if file_share == "":
				user_rec = request.user
			else:
				if not ShareUrl.objects.filter(url=file_share).exists():
					return JsonResponse({'result': 1})
				else:
					share_data = get_object_or_404(ShareUrl, url=file_share)
					user_rec = share_data.owner
			fm = FileManager(user_rec)
			fm.update_path(mkdir_form.cleaned_data['dir_path'])
			mkdir_status = fm.create_directory(mkdir_form.cleaned_data['dir_name'])
			if mkdir_status:
				return JsonResponse({'result': 0})
			else:
				return JsonResponse({'result': 2})
		else:
			return JsonResponse({'result': 1})
	else:
		# No get allowed
		return HttpResponseForbidden("Invalid Request")


def group_share(request):
	if request.method == 'POST':
		if 'lst' not in request.POST and 'del' not in request.POST:
			# Share
			group_form = GroupShareForm(request.POST)
			group_form.full_clean()
			if group_form.is_valid():
				# Form valid
				group_name = group_form.cleaned_data['groupname']
				can_edit_check = group_form.cleaned_data['can_edit']
				# Check if group available
				if Group.objects.filter(name=group_name).exists():
					# Share to group
					try:
						user = get_object_or_404(User, user_id=request.user.pk)
						grup = get_object_or_404(Group, name=group_name)
						# Check if user is a group member
						if UserGroup.objects.filter(group=grup, user=user).exists():
							if GroupShare.objects.filter(owner=user, group=grup, path=request.POST.get("fp", "")).exists():
								return JsonResponse({'result': 2})
							else:
								group_shr = GroupShare.objects.create(owner=user, group=grup, path=request.POST.get("fp", ""), can_edit=can_edit_check)
								if not group_shr:
									return JsonResponse({'result': 1})
								else:
									# Email group members
									grup_members = UserGroup.objects.filter(group=grup)
									for member in grup_members:
										if member.user != user:
											# Do not email myself											
											send_share_email(member.user.email, member.user.name, member.user.surname, user.name, user.surname,
												user.user_id, request.POST.get("fn", ""))
									return JsonResponse({'result': 0}) # Success
						else:
							return JsonResponse({'result': 3}) # Not a group member
					except Exception as ex:
						return JsonResponse({'result': 4})
				else:
					# Group does not exist
					return JsonResponse({'result': 1})
			else:
				return JsonResponse({'result': 4}) # Error
		elif 'del' in request.POST:
			# Unshare
			group_id = request.POST.get("del", None)
			if group_id is None:
				return JsonResponse({'result': 1}) # Error
			else:
				try:
					grup = get_object_or_404(Group, pk=group_id)
					sharer = get_object_or_404(User, user_id=request.user.pk)
					groupshare = get_object_or_404(GroupShare, owner=sharer, group=grup, path=request.POST.get("fp", ""))
					groupshare.delete()
					# Removal complete
					return JsonResponse({'result': 0})
				except Exception as ex:
					return JsonResponse({'result': 1}) # Error
		else:
			# Return share list
			group_share_list = GroupShare.objects.filter(owner=User(user_id=request.user.pk), path=request.POST.get("fp", "")).values("group__pk","group__name","can_edit")
			#json_data = serializers.serialize('json', group_share_list, fields=('name', 'edit'))
			json_data = json.dumps(list(group_share_list), cls=DjangoJSONEncoder)
			return HttpResponse(json_data, content_type='application/json')
	else:
		return HttpResponseForbidden()


def user_share(request):
	if request.method == 'POST':
		if 'lst' not in request.POST and 'del' not in request.POST:
			# Share
			user_form = UserShareForm(request.POST)
			user_form.full_clean()
			if user_form.is_valid():
				# Form valid
				user_name = user_form.cleaned_data['username']
				can_edit_check = user_form.cleaned_data['can_edit']
				# Check if group available
				if User.objects.filter(user_id=user_name).exists():
					# Share to user
					try:
						user = get_object_or_404(User, user_id=user_name)
						sharer = get_object_or_404(User, user_id=request.user.pk)
						if sharer == user:
							return JsonResponse({'result': 3}) # Cannot share with yourself
						else:
							if UserShare.objects.filter(owner=sharer, shared_with=user, path=request.POST.get("fp", "")).exists():
								return JsonResponse({'result': 2})
							else:
								user_shr = UserShare.objects.create(owner=sharer, shared_with=user, path=request.POST.get("fp", ""), can_edit=can_edit_check)
								if not user_shr:
									return JsonResponse({'result': 1})
								else:
									# Email user
									send_share_email(user.email, user.name, user.surname, sharer.name, sharer.surname, sharer.user_id, request.POST.get("fn", ""))
									return JsonResponse({'result': 0}) # Success
					except Exception as ex:
						return JsonResponse({'result': 4})
				else:
					# User does not exist
					return JsonResponse({'result': 1})
			else:
				return JsonResponse({'result': 4}) # Error
		elif 'del' in request.POST:
			# Unshare
			users_id = request.POST.get("del", None)
			if users_id is None:
				return JsonResponse({'result': 1}) # Error
			else:
				try:
					user = get_object_or_404(User, user_id=users_id)
					sharer = get_object_or_404(User, user_id=request.user.pk)
					usershare = get_object_or_404(UserShare, owner=sharer, shared_with=user, path=request.POST.get("fp", ""))
					usershare.delete()
					# Removal complete
					return JsonResponse({'result': 0})
				except Exception as ex:
					return JsonResponse({'result': 1}) # Error
		else:
			# Return share list
			user_share_list = UserShare.objects.filter(owner=User(user_id=request.user.pk), path=request.POST.get("fp", "")).values("shared_with__pk","shared_with__title",
				"shared_with__initials","shared_with__name","shared_with__surname","shared_with__email","can_edit")
			#json_data = serializers.serialize('json', User.objects.filter(user_id__in=user_share_list), fields=('title','initials','name','surname','email'))
			json_data = json.dumps(list(user_share_list), cls=DjangoJSONEncoder)			
			return HttpResponse(json_data, content_type='application/json')
	else:
		return HttpResponseForbidden()

@user_required
def public_share(request):
	if request.method == 'POST':
		if 'lst' not in request.POST:
			if ShareUrl.objects.filter(owner=User(user_id=request.user.pk), path=request.POST.get("filepath", "")).exists():
				# Delete link
				try:
					share_url = ShareUrl.objects.filter(owner=User(user_id=request.user.pk), path=request.POST.get("filepath", "")).values("url_id")
					share_url_link = ShareUrl.objects.filter(url__in=share_url)
					share_url_link.delete()		
					#share_url.delete()
				except Exception as ex:
					return JsonResponse({'result': 2})
				return JsonResponse({'result': 1})
			else:
				# Share
				#new_url = str(uuid.uuid4().hex[:16]) # Generate unique link
				new_url = str(get_random_string(length=12)) # Random share link
				while ShareUrl.objects.filter(url=new_url).exists():
					# Check if random url has not been used before
					new_url = str(get_random_string(length=12)) # Regenerate random share link
				try:
					user = get_object_or_404(User, user_id=request.user.pk)
					new_share_url = ShareUrl.objects.create(url=new_url, is_private=False)
					if new_share_url:
						new_share = ShareUrl.objects.create(owner=user, path=request.POST.get("filepath", None), url=new_share_url, can_edit=False)
						if new_share:
							return JsonResponse({'result': 0, 'sharelink': settings.EXTERNAL_URL + 's/' + new_url})
						else:
							return JsonResponse({'result': 2})
					else:
						return JsonResponse({'result': 2})
				except Exception as ex:
					return JsonResponse({'result': 2})
		else:
			# Return share list
			if ShareUrl.objects.filter(owner=User(user_id=request.user.pk), path=request.POST.get("filepath", "")).exists():
				share_url = ShareUrl.objects.filter(owner=User(user_id=request.user.pk), path=request.POST.get("filepath", "")).values_list("url_id", flat=True)[0]
				return JsonResponse({'result': 0, 'sharelink': settings.EXTERNAL_URL + 's/' + str(share_url)})
			else:
				return JsonResponse({'result': 1})
	else:
		return HttpResponseForbidden()


def public_access(request, share_url):
	if not ShareUrl.objects.filter(url=share_url).exists():
		return render(request, 'cloud/e404.html') # 404
	else:
		share_data = get_object_or_404(ShareUrl, url=share_url)
		fm = FileManager(share_data.owner)
		is_file = fm.set_share_path(share_data.path)
		if is_file == 1:
			# File details
			context = fm.file_details(share_data.path)
			context.update({'fileowner': share_data.owner, 'shareurl': share_url})
			return render(request, 'cloud/fileShare.html', context)
		else:
			# Directory Explorer
			mkdir_form = MkdirForm()
			upload_form = UploadForm()
			mkdir_form.initial['dir_path'] = share_data.path # Default path
			upload_form.initial['upload_path'] = share_data.path # Set defaiult path
			if 'p' in dict(request.GET) and len(dict(request.GET)['p'][0]) > 0:
				new_path = dict(request.GET)['p'][0].replace("../", "") # No previous directory browsing
				fm.update_path(new_path)
				mkdir_form.initial['dir_path'] = new_path
				upload_form.initial['upload_path'] = new_path
			mkdir_form.initial['share_url'] = share_url
			upload_form.initial['share_url'] = share_url
			context = {'files': fm.directory_list(), 'uploadForm': upload_form, 'mkdirForm': mkdir_form,
					'shareurl': share_url, 'canEdit': share_data.can_edit, 'sharelink': settings.EXTERNAL_URL + 's/' + share_url}
			fm.update_context_data(context)
			return render(request, 'cloud/directoryShare.html', context)


@user_required
def shared_with_me(request):
	context = {}
	return render(request, 'cloud/sharedBrowser.html', context)
