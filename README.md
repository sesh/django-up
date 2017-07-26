# django-up

`django-up` is a zero configuration [Django][django] deployment tool.


```shell
> ./manage.py up djangoup.com
```


Running `django-up` will deploy a production ready, SSL-enabled, Django application to a VPS using:

- Nginx
- OpenSMTPd
- Gunicorn
- PostreSQL
- Let's Encrypt
- UFW


With optional roles installing and configuring:

- Celery
- Memcached
- django-kronos (for running scheduled tasks)
- PhantomJS
- Redis
- New Relic


---

## Installation

For now it's best to add `django-up` to your project as a git submodule:

```shell
> git submodule add git@github.com:sesh/django-up.git up
```

(the `up` on the end there is vital - we want the submodule to be added as the `up` directory)

Add `up` install your `INSTALLED_APPS` to enable the management command.


---


## Getting Started

### Requirements

- [x] A fresh VPS that you can SSH to (as root)
- [x] Configure your Django application to use `dj_database_url`
- [x] Add a `requirements.txt` that installs any dependencies for your project
- [x] Install `pyyaml` into your project's virtual environment
- [x] Install `ansible` globally


### How to deploy your first site

1. Create a Django application using `django-admin startproject`.
2. Install `django-up`
3. Add `up` to your `INSTALLED_APPS`
4. Ensure that your requirements are in a `requirements.txt` file that lives next to your `manage.py` file
5. Update your `settings.py` file to use `dj_database_url` for your database configuration
6. Update your `settings.py` to include your domain name in `ALLOWED_HOSTS`
7. Run `./manage.py up <hostname>`


### Configuring dj_database_url

If you'd like to continue using SQLite3 locally you can set up your `DATABASES` like this:

```
import dj_database_url
DATABASES = {'default': dj_database_url.config(default='sqlite:///{}'.format(os.path.join(BASE_DIR, 'db.sqlite3')))}
```

If you want to use Postgres locally (good idea!) you still need to use dj_database_url, so check out the documentation and set it up properly for your needs.


### Setting environment variables

Add environment variables to a `.up-env` file alongside your `./manage.py`. These will be exported into the environment before running your server (and management commands).

---

## Roles

The following Ansible roles are always ran to build a standard Django stack:


### Nginx


### PostgreSQL


### Django


### OpenSMPTd


### SSL

SSL will be configured using Let's Encrypt and will automatically renew on a monthly basis. Unfortunately this means that `django-up` cannot be used to set up sites that allow wildcard subdomains. SSL is configured using the Modern configuration generated by the [Mozilla SSL Configuration Generator][moz-ssl] which means that IE10 is not supported.

Redirecting to HTTPS is handled by Django's SecurityMiddleware with the `SECURE_SSL_REDIRECT` setting - this means that you can disable the redirection by removing the SecurityMiddleware (this is a bad idea).


### Swap

To support deployments on the 512mb instances available on Digital Ocean we add a little bit of swap space. This allows us to reliably run `apt update && apt upgrade` without having to shut down the `gunicorn` instances.


---

## Monitoring

### New Relic

Enable support for New Relic by adding a `DJANGO_NEWRELIC_KEY` variable to your `.up-env` file.


---

## Extras

You can define `UP_EXTRAS` in your settings that will be included as part of your deployment.

```python
# include all available extras:
UP_EXTRAS = [
  'kronos',
  'redis',
  'phantomjs',
  'memcached',
  'celery',
]
```


### Kronos

`django-kronos` is a simple way to manage scheduled tasks with `cron`. `django-up` will automatically configure Kronos to use the virtualenv created for your project and add the Kronos cronjob to the crontab for the application user.

You need to include `kronos` in your `INSTALLED_APPS`.


### Redis


### PhantomJS


### Memcached


### Celery


---


## Important Notes

- Your `STATIC_ROOT`, `MEDIA_ROOT`, `DEBUG` and `SECURE_SSL_REDIRECT` settings will be overridden.
- You must list the full domains you'd like served in `ALLOWED_HOSTS`, no `.github.com` to include all subdomains.


---

## Support `django-up`

Want to play with `django-up` on a VPS? Use these affiliate links to sign up and I promise to spend the money on beer.

- [Digital Ocean](https://m.do.co/c/c1152c27c002)
- [Vultr](http://www.vultr.com/?ref=6899304)


[moz-ssl]: https://mozilla.github.io/server-side-tls/ssl-config-generator/
[django]: https://djangoproject.com
