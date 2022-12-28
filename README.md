# django-up

`django-up` is a tool to quickly deploy your Django application to a Ubuntu 22.04 server with almost zero configuration.

```shell
python manage.py up djangoup.com --email=<your-email>
```

Running `django-up` will deploy a production ready, SSL-enabled, Django application to a VPS using:

- Nginx
- Gunicorn
- Postres
- SSL with acme.sh (using Let's Encrypt)
- UFW
- OpenSMTPd


## Supporting this project

The easiest way to support the development of this project is to use [my Linode referal code][linode] if you need a hosting provider.
By using this link you will receive a $100, 60-day credit once a valid payment method is added.
If you spend $25 I will receive $25 credit in my account.

`django-up` costs around $7/month to host on Linode, referrals cover that cost, plus help to support my other projects hosted there. I've used various hosting providers over the last few years but Linode is the one that I like the most.

_This is the only place where referral codes are used. All other links in the documentation will take you to the services without my reference._


## Quick Start (with Pipenv)

Create a new VPS with your preferred provider and update your domain's DNS records to point at it. Check that you can SSH to the new server before continuing.

Ensure that `ansible` is installed on the system your are deploying from.

Create a directory for your new project and `cd` into it:

```shell
mkdir testproj
cd testproj
```

Install Django, PyYAML and dj_database_url:

```shell
pipenv install Django pyyaml dj_database_url
```

Start a new Django project:

```shell
pipenv run django-admin startproject testproj .
```

Run `git init` to initialise the new project as a git repository:

```shell
git init
```

Add `django-up` as a git submodule:

```shell
git submodule add git@github.com:sesh/django-up.git up
```

Add `up` to your `INSTALLED_APPS` to enable the management command:

```python
INSTALLED_APPS = [
  # ...
  'up',
]
```

Add your target domain to the `ALLOWED_HOSTS` in your `settings.py`.

```python
ALLOWED_HOSTS = [
  'djup-test.brntn.me',
  'localhost'
]
```

Set the `SECURE_PROXY_SSL_HEADER` setting in your `settings.py` to ensure the connection is considered secure.

```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_SCHEME', 'https')
```

Set up your database to use `dj_database_url`:

```python
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')
}
```

Create a requirements file from your environment if one doesn't exist:

```shell
pipenv lock -r > requirements.txt
```

Deploy with the `up` management command:

```shell
pipenv run python manage.py up yourdomain.example --email=<your-email>
```


## Extra Configuration

### Setting environment variables

Add environment variables to a `.env` file alongside your `manage.py`. These will be exported into the environment before running your server (and management commands during deployment).

For example, to configure Django to load the SECRET_KEY from your environment, and add a secure secret key to your `.env` file:

`settings.py`:

```python
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
```

`.env`:

```
DJANGO_SECRET_KEY="dt(t9)7+&cm$nrq=p(pg--i)#+93dffwt!r05k-isd^8y1y0"
```


### Specifying a Python version

By default, `django-up` uses Python 3.10.
If your application targets a different version you can use the `UP_PYTHON_VERSION` environment variable.
Valid choices are:

- `python3.8`
- `python3.9`
- `python3.10` (default)
- `python3.11`

```python
UP_PYTHON_VERSION = "python3.11"
```

These are the Python version available in the deadsnakes PPA.
Versions older than Python 3.8 require older versions of OpenSSL so are not included in the PPA for Ubuntu 22.04.


### Deploying multiple applications to the same server

Your application will bind to an internal port on your server.
To deploy multiple applications to the same server you will need to manually specify this port.

In your `settings.py`, set `GUNICORN_PORT` is set to a unique port for the server that you are deploying to:

```python
UP_GUNICORN_PORT = 8556
```


### Using manifest file storage

To minimise downtime, during the deployment `collectstatic` is executed while your previous deployment is still running.
In order make sure that the correct version of static files are used _during the deployment_ you can use the `ManifestStaticFilesStorage` storage backend that Django provides.

```python
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
```

For most projects using this backend will be a best practice, regardless of whether you are deploying with `django-up`.


### Supporting multiple domains

As long as all domains that you plan on supporting are pointing to your server, you can include them in your `ALLOWED_HOSTS`.
Certificates will be requested for each domain.

For example, so support both the apex and `www` subdomain for a project, your could configure your application with:

```python
ALLOWED_HOSTS = [
  'django-up.com',
  'www.django-up.com'
]
```


### Adding `django-up` directly to your project

If you are likely to customise the Ansible files then it's probably easier to just add the `django-up` files to your own git repository, rather than using a submodule.

You can use a shell one liner to download the repository from Github and extract it into an "up" directory in your project:

```shell
mkdir -p up && curl -L https://github.com/sesh/django-up/tarball/main | tar -xz --strip-components=1 -C up
```


  [django]: https://www.djangoproject.com
  [linode]: https://www.linode.com/lp/refer/?r=46340a230dfd33a24e40407c7ea938e31b295dec
