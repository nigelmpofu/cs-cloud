"""cs_cloud URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
	https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
	1. Add an import:  from my_app import views
	2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
	1. Add an import:  from other_app.views import Home
	2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
	1. Import the include() function: from django.urls import include, path
	2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from cloud import views, adminViews, userViews

urlpatterns = [
	#path('admin/', admin.site.urls),
	path('robots.txt', views.robots_txt, name="robotsTxt"),
	path('', views.index, name='index'),
	path('login/', views.login, name='login'),
	path('auth/login/', views.auth, name='auth'),
	path('auth/logout/', views.auth_logout, name='logout'),
	path('auth/forgotPassword/', views.forgot_password, name='forgotPassword'),
	path('auth/recoverPassword/', views.recover_password, name="recoverPassword"),
	path('auth/resetPassword/', views.reset_password, name="resetPassword"),
	path('auth/resetPassword/<str:user_id>/<slug:token>/', views.reset_password_token, name="resetPasswordToken"),
	
	# Admin URL
	path('admin/diskUsage/', adminViews.disk_usage, name="diskUsage"),
	path('admin/userAdmin/', adminViews.user_admin, name="userAdmin"),
	path('admin/userAdmin/submitUser/', adminViews.submit_user, name="submitUser"),
	path('admin/userAdmin/checkUser/', adminViews.check_user, name="checkUser"),
	path('admin/userAdmin/editUser/', adminViews.edit_user, name="adminEditUser"),
	path('admin/userAdmin/deleteUser/', adminViews.users_delete, name="adminDeleteUser"),
	path('admin/userAdmin/resetPassword/', adminViews.admin_reset_password, name="adminResetPassword"),
	path('admin/files/', adminViews.admin_files, name="adminFiles"),
]
