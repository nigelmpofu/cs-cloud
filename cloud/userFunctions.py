import base64
from smtplib import SMTPException

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.signing import TimestampSigner
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

# Sign and urlsafe Base64 encode a user ID with
# a timestamp. Returns result as string
def sign_user_id(user_id):
    id_signer = TimestampSigner()
    signed = id_signer.sign(user_id)

    b64encoded = base64.urlsafe_b64encode(signed.encode('utf-8'))
    return b64encoded.decode('utf-8')

# Unsign a given url-save base64 encoded userId
# to a string. Returns the user id if successful;
# on failure, returns None. This function can fail
# when the encoded userId has expired (max age) or
# the signed key is invalid.
def unsign_user_id(b64_user_id, max_age=None):
    try:
        id_signer = TimestampSigner()
        unencoded_user_id = base64.urlsafe_b64decode(b64_user_id.encode('utf-8')).decode('utf-8')
        signed = id_signer.unsign(unencoded_user_id, max_age)
        return signed.split(':', 1)[0]
    except Exception as e:
        #print(e)
        return None
