from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout
from cloud.decorators.adminRequired import admin_required
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from .tokens import tokenizer
from .forms import LoginForm
from .forms import RecoverPasswordForm
from .forms import ResetForm
from .mailer import send_password_request_email
from .models import User

@admin_required
def user_admin(request):
	return HttpResponse("Hello")