from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout
from cloud.decorators.adminRequired import admin_required
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
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