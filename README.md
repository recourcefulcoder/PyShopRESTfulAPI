# PyShopRESTfulAPI
Test task for PyShop internship

Database specified for the project is PostgreSQL, so your server/local machine should have PostgreSQL 
server enabled so that application can function

You should also have redis-server installed and running; if you a running on a Linux machine, you can install it
by running following in your CLI:
```bash
sudo apt-get update
sudo apt-get install redis-server
```

and for running simply use

```bash
redis-server
```

#### Environmental variables
+ **DJANGO_SECRET_KEY** - secret key used for cryptographical purposes
+ **DJANGO_DEBUG** - specifies whether application should run in DEBUG mode or not
+ **DJANGO_HOST** - specifies host to run database on; defaults to "localhost"
+ **DJANGO_DB_PASSWORD** - password for connecting to the PosgtreSQL database
+ **DJANGO_DB_USERNAME** - db username value
+ **DJANGO_DB_NAME** - database name