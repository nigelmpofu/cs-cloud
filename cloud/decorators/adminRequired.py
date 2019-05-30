from django.shortcuts import redirect

def admin_check(user):
	if user.is_active and user.is_authenticated:
		if user.is_user_admin:
			return True
	return False


def admin_required(function=None, redirect_field_name=None, login_url='/login/'):
	"""
	Decorator for views that checks that the user is logged in
	and has the "admin" permission set.
	"""

	def _decorated(view_func):
		def _view(request, *args, **kwargs):
			if admin_check(request.user):
				return view_func(request, *args, **kwargs)
			else:
				# Not admin
				return redirect(login_url)

		_view.__name__ = view_func.__name__
		_view.__dict__ = view_func.__dict__
		_view.__doc__ = view_func.__doc__

		return _view

	if function is None:
		return _decorated
	else:
		return _decorated(function)