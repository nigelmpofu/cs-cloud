import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout
from cloud.decorators.userRequired import user_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .tokens import tokenizer
from .forms import LoginForm, MkdirForm, RecoverPasswordForm, ResetForm, UploadForm
from .mailer import send_password_request_email
from .models import User
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
			os.mkdir(user_directory)
		except OSError:
			messages.error(request, "Error accessing your data.<br/>Contact admin")
			logout(request)
			return redirect("index")
	fm = FileManager(request.user)
	mkdir_form = MkdirForm()
	upload_form = UploadForm()
	if 'p' in dict(request.GET) and len(dict(request.GET)['p'][0]) > 0:
		new_path = dict(request.GET)['p'][0].replace("../", "") # No previous directory browsing
		fm.update_path(new_path)
		mkdir_form.initial['dir_path'] = new_path
		upload_form.initial['upload_path'] = new_path
	context = {'files': fm.directory_list(), 'uploadForm': upload_form, 'mkdirForm': mkdir_form}
	fm.update_context_data(context)
	return render(request, 'cloud/fileManager.html', context)


def file_browser(request):
	# Todo: file handling, sharing and security
	return HttpResponse("File: " + request.GET.get("f"))


def file_details(request):
	if request.method == 'POST':
		fm = FileManager(request.user)
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


def file_download(request):
	fm = FileManager(request.user)
	return fm.download_file(request.GET.get("file"))


def check_quota(request):
	return JsonResponse({'available': request.user.get_remaining_quota()})


def file_upload(request):
	if request.method == 'POST':
		upload_form = UploadForm(request.POST, request.FILES)
		upload_form.full_clean()
		user_files = request.FILES.getlist('user_files')
		if upload_form.is_valid():
			fm = FileManager(request.user)
			fm.update_path(upload_form.cleaned_data['upload_path'])
			user_db = get_object_or_404(User, pk=request.user.user_id)
			insufficient_count = 0
			for file_to_upload in user_files:
				user_db = get_object_or_404(User, pk=request.user.user_id)
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
			fm = FileManager(request.user)
			fm.update_path(mkdir_form.cleaned_data['dir_path'])
			print(mkdir_form.cleaned_data['dir_path'])
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