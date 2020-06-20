# cs-cloud

File storage and sharing service built on the Django framework.

-------------

## Installation Instructions

- Clone the CS-Cloud repository and `cd` into it
  - `git clone https://github.com/nigelmpofu/cs-cloud.git`
  - `cd cs-cloud`
- _(Recommended)_ Create a new Python 3 virtual environment
  - Create it: `python3 -m venv ./venv`
  - Activate it: `source ./venv/bin/activate`
- Install Django **2.2.13** and other packages [python 3.5+ required]
  - `pip3 install -r ./requirements.txt`
- Apply Database Migrations
  - `python3 manage.py migrate`
- Create root user
  - `python3 manage.py createsuperuser`
- Run the server
  - `python3 manage.py runserver`

## Email Configuration

In order to enable email functionality:

- Add email server configuration to the `config.py` file located in the `cs_cloud` directory.
- Leave `EMAIL_HOST` blank to diable email functionality.
- If the `DEBUG` flag is set in `settings.py` then emails will also be printed to the console.
 _Note: Loading may be delayed while attempting to send emails on a slow Internet connection._
