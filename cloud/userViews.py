import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout
from cloud.decorators.userRequired import user_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .tokens import tokenizer
from .forms import LoginForm, RecoverPasswordForm, ResetForm, UploadForm
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
	if not os.path.exists(user_directory):
		try:
			os.mkdir(user_directory)
		except OSError:
			messages.error(request, "Error accessing your data.<br/>Contact admin")
			logout(request)
			return redirect("index")
	fm = FileManager(request.user)
	upload_form = UploadForm()
	context = {'files': fm.directory_list(), 'uploadForm': upload_form}
	return render(request, 'cloud/fileManager.html', context)


def file_browser(request):
	# Todo: file handling, sharing and security
	return HttpResponse("File: " + request.GET.get("f"))


def file_download(request):
	fm = FileManager(request.user)
	return fm.download_file(request.GET.get("file"))

def file_upload(request):
	if request.method == 'POST':
		upload_form = UploadForm(request.POST, request.FILES)
		upload_form.full_clean()
		user_files = request.FILES.getlist('user_files')
		if upload_form.is_valid():
			for f in user_files:
				# Do something with each file.
				print(f)
			messages.success(request, "Files uploaded successfully")
			return JsonResponse({'result': 0})
		else:
			messages.error(request, "Files could not be uploaded")
			return JsonResponse({'result': 1})		
	else:
		# No get allowed
		return HttpResponseForbidden("Upload Rejected")