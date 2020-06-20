"""
Default disk quota assigned to each new user
Units: Bytes (Base 2 - 1 kiB = 1024 bytes)
Default: 100 MiB
Note: Make migrations when updating value
"""
DEFAULT_QUOTA = 104857600

"""
How long the 'Change Password' URL should be
valid, in days.
Current: 1 day (24 Hours)
"""
PASSWORD_RESET_TIMEOUT_DAYS = 1

"""
External server url
TODO: CHANGE IN PRODUCTION
"""
#EXTERNAL_URL = 'http://cloud.domain.com/'
EXTERNAL_URL = 'http://127.0.0.1:8000/'

"""
Email settings
Note: Leave EMAIL_HOST blank to disable sending emails.
TODO: CHANGE IN PRODUCTION
"""
FROM_EMAIL_ADDRESS = 'CS Cloud <cs_cloud@example.com>'
EMAIL_USE_TLS = True
EMAIL_HOST = ""
EMAIL_PORT = 25
EMAIL_HOST_USER = "cs_cloud"
EMAIL_HOST_PASSWORD = "Cs.cl0ud.p@ssw0rd"
