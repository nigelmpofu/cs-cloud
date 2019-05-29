from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

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
	status = models.CharField(max_length=1)

	USERNAME_FIELD = 'user_id'
	REQUIRED_FIELDS = ['email']

	is_staff = models.BooleanField(default=False) # Admin User
	is_active = models.BooleanField(default=True, help_text='Designates whether this user should be treated as active.'
															'Deselect this instead of deleting accounts.')

	disk_quota = models.IntegerField(default=128, help_text='Available disk quota in megabytes.')
	used_quota = models.IntegerField(default=0, help_text='Used disk quota in megabytes.')

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
		return self.disk_quota - self.used_quota

