# django-up

`django-up` is a zero configuration [Django][django] deployment tool to deploy Django Projects to a Ubuntu 20.04 LTS environment.


```shell
> ./manage.py up djangoup.com
```

Running `django-up` will deploy a production ready, SSL-enabled, Django application to a VPS using:

- Nginx
- Gunicorn
- PostreSQL
- Let's Encrypt
- UFW
- OpenSMTPd


## Setup

Ensure that `ansible` is installed globally.

Add `django-up` as a git submodule:

```shell
> git submodule add git@github.com:sesh/django-up.git up
```

Install `pyyaml` and `dj_database_url` as dependencies in your project.

Add `up` install your `INSTALLED_APPS` to enable the management command:

```python
INSTALLED_APPS = [
  'up',
  # ...
]
```

Add your target domain to the `ALLOWED_HOSTS` in your `settings.py`.

Set up your database to use `dj_database_url`:

```python
import dj_database_url
DATABASES = {'default': dj_database_url.config(default=f'sqlite:///{BASE_DIR, 'db.sqlite3'}')}
```

Make sure that `GUNICORN_PORT` is set to a unique port for the server that you are deploying to:

```python
GUNICORN_PORT = 5566
```

Deploy with the `up` management command:

```shell
> ./manage.py up yourdomain.example
```


### Setting environment variables

Add environment variables to a `.up-env` file alongside your `./manage.py`. These will be exported into the environment before running your server (and management commands).


  [djanog]: https://www.djangoproject.com