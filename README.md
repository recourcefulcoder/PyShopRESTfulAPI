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

To run an application (assuming you have already switched to outer api_service directory):
1. Download all the dependencies
```bash
pip install -r requirements/dev_req.txt
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

+ **DJANGO_DB_ENGINE** - Django ORM engine for accessing database; defaults to "postgresql" (no brackets)
+ **DJANGO_DB_PORT** - port for database connection; defaults to 5432 (postgresql default)
+ **DJANGO_DB_HOST** - specifies host to run database on; defaults to "localhost"
+ **DJANGO_DB_PASSWORD** - password for connecting to the PosgtreSQL database
+ **DJANGO_DB_USERNAME** - db username value
+ **DJANGO_DB_NAME** - database name

In order to run DJANGO in production mode, you should add following environment variables:
+ DJANGO_ALLOWED_HOSTS - comma-separated list of values for [ALLOWED_HOSTS](https://docs.djangoproject.com/en/5.1/ref/settings/#std-setting-ALLOWED_HOSTS)
Django variable
+ DJANGO_CSRF_TRUSTED_ORIGINS - should be set to localhost:8001 for compatibility with nginx config file;
comma-separated list of values for [CSRF_TRUSTED_ORIGINS](https://docs.djangoproject.com/en/5.1/ref/settings/#csrf-trusted-origins)
Django variable; 

#### Auth notes
Chosen authentication model - JWT; _sub_ value of JWT token's payload is user's email.