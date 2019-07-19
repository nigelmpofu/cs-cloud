import logging
from smtplib import SMTPException

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

# Sends a password-reset email containing a signed
# Returns a boolean;
# True = email sent,
# False = error
def send_password_request_email(user_token, user_id, email_address, user_name, user_surname, new_account, user_otp=None):
	try:
		fn = "{first_name}"
		ln = "{last_name}"
		url = "{url}"
		usn = "{username}"
		otpstr = "{otp}"

		request_url = settings.EXTERNAL_URL + 'auth/resetPassword/' + user_id + '/' + user_token

		if new_account:
			file_path = settings.BASE_DIR + '/cloud/email_template/new_account.txt'
			email_subject = "CS Cloud Account Created"
		else:
			file_path = settings.BASE_DIR + '/cloud/email_template/password_request.txt'
			email_subject = "CS Cloud Password Reset Request"

		file = open(file_path, 'a+')
		file.seek(0)
		email_text = file.read()
		file.close()

		email_text = email_text.replace(fn, user_name)
		email_text = email_text.replace(ln, user_surname)
		email_text = email_text.replace(url, request_url)
		email_text = email_text.replace(usn, user_id)
		if new_account:
			email_text = email_text.replace(otpstr, user_otp)

		if settings.DEBUG:
			# Print email to terminal for debugging purposes
			print(email_text)

		# Emails are sent here
		if settings.EMAIL_HOST != "":
			send_mail(email_subject, email_text, settings.FROM_EMAIL_ADDRESS, [email_address], fail_silently=False)
		else:
			logger.warning("No EMAIL_HOST configured; Did not attempt to send email.")

		return True
	except SMTPException as e:
		logger.error('Error while sending email: ' + str(e))
		#raise e
		return False


def send_share_email(email_address, user_name, user_surname, sharer_name, sharer_surname, sharer_id, shared_file):
	try:
		fn = "{first_name}"
		ln = "{last_name}"
		sfn = "{sfirst_name}"
		sln = "{slast_name}"
		sid = "{username}"
		sfl = "{share_item}"

		file_path = settings.BASE_DIR + '/cloud/email_template/file_shared.txt'
		email_subject = "File Shared With You"

		file = open(file_path, 'a+')
		file.seek(0)
		email_text = file.read()
		file.close()

		email_text = email_text.replace(fn, user_name)
		email_text = email_text.replace(ln, user_surname)
		email_text = email_text.replace(sfn, sharer_name)
		email_text = email_text.replace(sln, sharer_surname)
		email_text = email_text.replace(sid, sharer_id)
		email_text = email_text.replace(sfl, shared_file)

		if settings.DEBUG:
			# Print email to terminal for debugging purposes
			print(email_text)

		# Emails are sent here
		if settings.EMAIL_HOST != "":
			send_mail(email_subject, email_text, settings.FROM_EMAIL_ADDRESS, [email_address], fail_silently=False)
		else:
			logger.warning("No EMAIL_HOST configured; Did not attempt to send email.")

		return True
	except SMTPException as e:
		logger.error('Error while sending email: ' + str(e))
		#raise e
		return False


def send_account_activity(email_address, user_name, user_surname, user_id, action_type):
	'''
	action_type
	0 - Account Edited
	1 - Account Deleted
	'''
	try:
		fn = "{first_name}"
		ln = "{last_name}"
		uid = "{user_id}"

		file_path = ""
		if action_type == 0:
			file_path = settings.BASE_DIR + '/cloud/email_template/account_changes.txt'
			email_subject = "CS Cloud Account Changes"
		else:
			file_path = settings.BASE_DIR + '/cloud/email_template/account_deleted.txt'
			email_subject = "CS Cloud Account Deleted"

		file = open(file_path, 'a+')
		file.seek(0)
		email_text = file.read()
		file.close()

		email_text = email_text.replace(fn, user_name)
		email_text = email_text.replace(ln, user_surname)
		email_text = email_text.replace(uid, user_id)

		if settings.DEBUG:
			# Print email to terminal for debugging purposes
			print(email_text)

		# Emails are sent here
		if settings.EMAIL_HOST != "":
			send_mail(email_subject, email_text, settings.FROM_EMAIL_ADDRESS, [email_address], fail_silently=False)
		else:
			logger.warning("No EMAIL_HOST configured; Did not attempt to send email.")

		return True
	except SMTPException as e:
		logger.error('Error while sending email: ' + str(e))
		#raise e
		return False


def send_group_activity(email_address, user_name, user_surname, user_id, group_name, action_type):
	'''
	action_type
	0 - User Added
	1 - User Removed
	2 - Group Deleted
	'''
	try:
		fn = "{first_name}"
		ln = "{last_name}"
		uid = "{user_id}"
		sgn = "{group_name}"

		file_path = ""
		if action_type == 0:
			file_path = settings.BASE_DIR + '/cloud/email_template/group_add.txt'
			email_subject = "You have been added to a group"
		elif action_type == 1:
			file_path = settings.BASE_DIR + '/cloud/email_template/group_remove.txt'
			email_subject = "You have been removed from a group"
		else:
			file_path = settings.BASE_DIR + '/cloud/email_template/group_deleted.txt'
			email_subject = "A group you are a member of has been deleted"

		file = open(file_path, 'a+')
		file.seek(0)
		email_text = file.read()
		file.close()

		email_text = email_text.replace(fn, user_name)
		email_text = email_text.replace(ln, user_surname)
		email_text = email_text.replace(uid, user_id)
		email_text = email_text.replace(sgn, group_name)

		if settings.DEBUG:
			# Print email to terminal for debugging purposes
			print(email_text)

		# Emails are sent here
		if settings.EMAIL_HOST != "":
			send_mail(email_subject, email_text, settings.FROM_EMAIL_ADDRESS, [email_address], fail_silently=False)
		else:
			logger.warning("No EMAIL_HOST configured; Did not attempt to send email.")

		return True
	except SMTPException as e:
		logger.error('Error while sending email: ' + str(e))
		#raise e
		return False
