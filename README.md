# PyShopRESTfulAPI
Test task for PyShop internship


#### Run in development mode instructions

> [!WARNING]
> in order to run in dev-mode, your DJANGO_DEBUG env variable should be set to True

Database specified for the project is PostgreSQL, so your server/local machine should have PostgreSQL 
server enabled so that application can function

You should also have redis-server installed; if you a running on a Linux machine, you can install it
by running following in your CLI:
```bash
sudo apt-get update
sudo apt-get install redis-server
```

In dev-mode (i.e. when settings.DEBUG is set to **True**) redis-sevrer is ran automatically; however,
in prod mode you should take care of that on yourself.

To run an application (asssuming you have switched to main directory):
1. Download all the dependencies
```bash
pip install -r requirements/dev.txt
```
2. Apply database migrations
```bash
python manage.py migrate 
```
3. Run the service
```bash
python manage.py runserver
```

#### Environmental variables
+ **DJANGO_SECRET_KEY** - secret key used for cryptographical purposes
+ **DJANGO_DEBUG** - specifies whether application should run in DEBUG mode or not
+ **DJANGO_HOST** - specifies host to run database on; defaults to "localhost"
+ **DJANGO_DB_PASSWORD** - password for connecting to the PosgtreSQL database
+ **DJANGO_DB_USERNAME** - db username value
+ **DJANGO_DB_NAME** - database name


#### Auth notes
Chosen authentication model - JWT; sub value of JWT token is user's email.