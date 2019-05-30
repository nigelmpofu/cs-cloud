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

