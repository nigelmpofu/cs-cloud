from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout
from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from .userFunctions import unsign_user_id, sign_user_id
from .forms import LoginForm
from .forms import RecoverPasswordForm
from .models import User


def login(request):
    logout(request)
    login_form = LoginForm()
    context = {'loginForm': login_form}
    return render(request, 'cloud/login.html', context)


def index(request):
    return login(request)


def auth(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user_id = request.POST.get('userName')
            password = request.POST.get('password')
            user = authenticate(user_id=user_id, password=password)
            if user:
                if user.is_active:
                    # Redirect if OTP is set
                    if User.objects.get(user_id=user_id).OTP:
                        request.user = user
                        return change_password(request)
                    # return change_password_request(request, user_id, password)
                    django_login(request, user)
                    # Redirect based on user account type
                    if user.is_staff or user.is_superuser:
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


def recover_password(request, key):
    if request.method == 'GET':
        # Test if the key is still valid
        user_id = unsign_user_id(key, settings.FORGOT_PASSWORD_AGE)
        if not user_id:
            messages.error(request, 'The link has expired or is invalid. Please generate a new one.')
            return redirect('recoverPassword')

        context = {}

        try:
            user = User.objects.get(user_id=user_id)
            context['name'] = user.name
            context['surname'] = user.surname

        except Exception as e:
            print(e)

        form = RecoverPasswordForm(request.user, url_token=key)
        context['form'] = form
        return render(request, 'cloud/passwordChange.html', context)

    if request.method == 'POST':
        new_form = RecoverPasswordForm(request.user, None, request.POST)
        new_form.full_clean()
        key = new_form.cleaned_data['urlTokenField']
        for err, description in new_form.errors.items():
            messages.error(request, description)

        # If the form is valid, go ahead and change the user's password.
        if new_form.is_valid():
            try:
                user_id = unsign_user_id(key, settings.FORGOT_PASSWORD_AGE)
                if not user_id:
                    messages.error(request, 'The link has expired or is invalid. Please generate a new one.')
                    return redirect('forgotPassword')

                user = User.objects.get(user_id=user_id)
                user.set_password(new_form.cleaned_data['new_password1'])
                user.OTP = False
                user.save()
                messages.success(request, "Success! Please log in with your new password")
                return redirect("login")

            except User.DoesNotExist:
                messages.error(request, "Your username seems to be invalid. This is not supposed to happen. "
                                        + "Please contact admin if problem persists.")
                return redirect("login")

            except Exception as e:
                print(e)
                messages.error(request, "There was a problem changing your password. Please try again.")
                return redirect("forgotPassword")

        return redirect('recoverPassword', key=key)


def change_password(request):
    user = request.user
    key = sign_user_id(user.user_id)
    request.method = 'GET'
    return recover_password(request, key)
