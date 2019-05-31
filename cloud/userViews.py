import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout
from cloud.decorators.userRequired import user_required
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from .tokens import tokenizer
from .forms import LoginForm
from .forms import RecoverPasswordForm
from .forms import ResetForm
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
	context = {'files': fm.directory_list()}
	return render(request, 'cloud/fileManager.html', context)


def file_browser(request):
	# Todo: file handling, sharing and security
	return HttpResponse("File: " + request.GET.get("f"))


def file_download(request):
	fm = FileManager(request.user)
	return fm.download_file(request.GET.get("file"))
