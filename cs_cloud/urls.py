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
	path('admin/diskUsage/data/', adminViews.disk_data, name="diskData"),
	path('admin/groupAdmin/', adminViews.group_admin, name="groupAdmin"),
	path('admin/groupAdmin/addMember/', adminViews.add_group_member, name="addGroupMember"),
	path('admin/groupAdmin/removeMember/', adminViews.remove_group_member, name="removeGroupMember"),
	path('admin/groupAdmin/checkGroup/', adminViews.check_group, name="checkGroup"),
	path('admin/groupAdmin/deleteGroup/', adminViews.delete_group, name="adminDeleteGroup"),
	path('admin/groupAdmin/listGroup/', adminViews.list_group, name="adminListGroup"),
	path('admin/groupAdmin/listMembers/', adminViews.list_members, name="listGroupMembers"),
	path('admin/groupAdmin/newGroup/', adminViews.new_group, name="submitGroup"),
	path('admin/userAdmin/', adminViews.user_admin, name="userAdmin"),
	path('admin/userAdmin/submitUser/', adminViews.submit_user, name="submitUser"),
	path('admin/userAdmin/checkUser/', adminViews.check_user, name="checkUser"),
	path('admin/userAdmin/editUser/', adminViews.edit_user, name="adminEditUser"),
	path('admin/userAdmin/deleteUser/', adminViews.users_delete, name="adminDeleteUser"),
	path('admin/userAdmin/resetPassword/', adminViews.admin_reset_password, name="adminResetPassword"),
	
	# File URLS
	path('files/', userViews.file_explorer, name="fileExplorer"),
	path('files/search/', userViews.file_search, name="fileSearch"),
	path('files/trash/', userViews.trash_explorer, name="trashExplorer"),
	path('files/trash/delete/', userViews.file_delete_perm, name="permDelete"),
	path('files/trash/empty/', userViews.empty_trash, name="emptyTrash"),
	path('file/', userViews.file_browser, name="fileBrowser"),
	path('file/delete/', userViews.file_delete, name="fileDelete"),
	path('file/details/', userViews.file_details, name="fileDetails"),
	path('file/download/', userViews.file_download, name="fileDownload"),
	path('file/move/', userViews.file_move, name="fileMove"),
	path('file/rename/', userViews.file_rename, name="fileRename"),
	path('file/restore/', userViews.file_restore, name="fileRestore"),
	path('file/upload/', userViews.file_upload, name="fileUpload"),
	path('file/upload/checkQuota/', userViews.check_quota, name="checkQuota"),
	path('file/mkdir/', userViews.create_directory, name="createDirectory"),
	path('file/gshare/', userViews.group_share, name="groupShare"),
	path('file/ushare/', userViews.user_share, name="userShare"),
	path('file/pshare/', userViews.public_share, name="publicShare"),

	# Public Link
	path('s/<str:share_url>/', userViews.public_access, name="publicAccess"),
	path('swm/', userViews.shared_with_me, name="sharedWithMe"),
	path('swma/<str:share_url>/', userViews.private_access, name="swmAccess")
]
