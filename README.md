# cs-cloud
File storage and sharing service that will be used by the CS department staff at the University of Pretoria.

-------------

### Installation Instructions
- Clone the CS-Cloud repository and `cd` into it
    - `git clone https://github.com/nigelmpofu/cs-cloud.git`
    - `cd cs-cloud`
- Install Django **2.2.1** and other packages
    - `pip3 install -r ./requirements.txt`
- Apply Database Migrations
    - `python manage.py migrate`
- Create root user
    - `python manage.py createsuperuser` 
- Run the server
    - `python manage.py runserver`