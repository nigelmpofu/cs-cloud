# cs-cloud
File storage and sharing service that will be used by the CS department staff at the University of Pretoria.

-------------

### Installation Instructions
- Clone the CS-Cloud repository and `cd` into it
    - `git clone https://github.com/nigelmpofu/cs-cloud.git`
    - `cd cs-cloud`
- Install Django **2.2.1** and other packages [python 3.5+ required]
    - `pip3 install -r ./requirements.txt`
- Apply Database Migrations
    - `python3 manage.py migrate`
- Create root user
    - `python3 manage.py createsuperuser` 
- Run the server
    - `python3 manage.py runserver`