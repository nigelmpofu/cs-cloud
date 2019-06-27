from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import math

class UserManager(BaseUserManager):
	def create_user(self, email, password, name, surname, **kwargs):
		user = self.model(
			email=self.normalize_email(email),
			is_active=True,
			name=name,
			surname=surname,
			**kwargs
		)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password, **kwargs):
		user = self.model(
			email=email,
			is_staff=True,
			is_superuser=True,
			is_active=True,
			OTP=False,
			**kwargs
		)
		user.set_password(password)
		user.save(using=self._db)
		return user


class User(AbstractBaseUser, PermissionsMixin):
	title = models.CharField(max_length=4)
	initials = models.CharField(max_length=10)
	name = models.CharField(max_length=50)
	surname = models.CharField(max_length=50)
	cell = models.CharField(max_length=10)
	email = models.EmailField(max_length=254)

	user_id = models.CharField(max_length=12, primary_key=True)
	OTP = models.BooleanField(default=True)

	USERNAME_FIELD = 'user_id'
	REQUIRED_FIELDS = ['email']

	is_staff = models.BooleanField(default=False) # Admin User
	is_active = models.BooleanField(default=True, help_text='Designates whether this user should be treated as active.'
															'Deselect this instead of deleting accounts.')

	disk_quota = models.BigIntegerField(default=settings.DEFAULT_QUOTA, help_text='Available disk quota in bytes.')
	used_quota = models.BigIntegerField(default=0, help_text='Used disk quota in bytes.')

	objects = UserManager()

	def get_email(self):
		"""Return the email."""
		return self.email

	def get_full_name(self):
		"""Return the users name."""
		return self.initials + " " + self.surname

	def is_user_admin(self):
		"""Return the admin status of a user."""
		return self.is_staff or self.is_superuser

	def get_remaining_quota(self):
		"""Returns the remaining available quota."""
		if self.disk_quota == 0:
			# Unlimited storage
			return math.inf
		else:
			return self.disk_quota - self.used_quota


def get_user_directory(instance, filename):
	# File stored in data/<user_id>/file
	return '{0}/{1}'.format(instance.user.user_id, filename)


class UserData(models.Model):
	owner = models.ForeignKey(User, on_delete=models.CASCADE)
	data = models.FileField(upload_to=get_user_directory)
	uploaded = models.DateTimeField(auto_now_add=True)

	@property
	def filename(self):
		fname = self.data.name.split("/")[1].replace('_',' ').replace('-',' ')
		return fname


class Group(models.Model):	
	name = models.CharField(max_length=32, default="new_group")


class UserGroup(models.Model):
	group = models.ForeignKey(Group, related_name="group", on_delete=models.CASCADE, null=False)
	user = models.ForeignKey(User, related_name="user", on_delete=models.CASCADE, null=False)


class PublicShare(models.Model):
	url = models.CharField(max_length=32, primary_key=True)
	owner = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
	path = models.CharField(max_length=256, default="", null=False)
