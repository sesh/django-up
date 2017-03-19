from __future__ import print_function

import os
import shutil
import string
import subprocess
import sys
import tempfile
import yaml

import requests

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

"""
Deploying Django applications as quickly as you create them

Usage:
    ./manage.py up <hostname>... [--debug] [--python2]

Your application needs to be configured to use dj_database_url and include your
target domain in ALLOWED_HOSTS.

nginx will be configured to serve
"""

class Command(BaseCommand):
    help = 'Deploy your Django site to a remote server'

    def add_arguments(self, parser):
        parser.add_argument('hostnames', nargs='+', type=str)
        parser.add_argument('--domain', nargs=1, type=str)
        parser.add_argument('--debug', action='store_true', default=False, dest='debug')
        parser.add_argument('--quick', action='store_true', default=False, dest='quick')
        parser.add_argument('--ssl', action='store_true', default=False, dest='ssl')
        parser.add_argument('--python2', action='store_true', default=False, dest='python2')
        parser.add_argument('--verbose', action='store_true', default=False, dest='verbose')
        parser.add_argument('--dont-force-ssl', action='store_true', default=False, dest='dont_force_ssl')

    def handle(self, *args, **options):
        ansible_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'ansible')
        hostnames = options['hostnames']
        app_name = settings.WSGI_APPLICATION.split('.')[0]

        up_dir = tempfile.TemporaryDirectory().name + '/django_up'
        app_tar = tempfile.NamedTemporaryFile(suffix='.tar')

        # copy our ansible files into our up_dir
        shutil.copytree(ansible_dir, up_dir)

        django_environment = {}
        try:
            with open(os.path.join(settings.BASE_DIR, '.up-env')) as env_file:
                for line in env_file.readlines():
                    if line and '=' in line and line.strip()[0] not in ['#', ';']:
                        var, val = line.split('=', 2)
                        if ' ' not in var:
                            django_environment[var] = val.strip()
                        else:
                            print('Ignoring environment variable with space: ', line)
            print('Loaded environment from .up-env: ', django_environment)
        except FileNotFoundError:
            pass

        # create a tarball of our application code
        subprocess.call([
            'tar',
            '--exclude', '*.pyc',
            '--exclude', '.git',
            '--exclude', '*.sqlite3',
            '--exclude', '__pycache__',
            '--exclude', '{}.tar'.format(app_name),
            '--dereference',
            '-cf', app_tar.name, '.'
        ])

        # use allowed_hosts to set up our domain names
        domains = []

        if options['domain']:
            domains = options['domain']
        else:
            for host in settings.ALLOWED_HOSTS:
                if host.startswith('.'):
                    domains.append('*' + host)
                elif '.' in host:
                    domains.append(host)

        print('Domains (ALLOWED_HOSTS or --domain): ', domains)

        for h in hostnames:
            if h not in domains:
                sys.exit("{} isn't in allowed domains".format(h))

        # database settings
        db_pass = str(get_random_string(12, string.ascii_letters + string.digits))
        db_url = 'postgres://{}:{}@localhost:5432/{}'.format(app_name, db_pass, app_name)
        django_environment['DATABASE_URL'] = db_url

        yam = [{
            'hosts': app_name,
            'remote_user': 'root',
            'gather_facts': 'yes',
            'vars': {
                'app_name': app_name,
                'service_name': app_name.replace('_', ''),
                'domain_names': ' '.join(domains),
                'gunicorn_port': getattr(settings, 'GUNICORN_PORT', '9000'),
                'app_tar': app_tar.name,
                'python_version': getattr(settings, 'UP_PYTHON_VERSION', 'python3.5'),
                'db_password': db_pass,
                'django_debug': 'yes' if options['debug'] else 'no',
                'django_environment': django_environment,
                'csr_domains': ','.join(['DNS:{}'.format(domain) for domain in domains]),
                'extra_app_dirs': getattr(settings, 'UP_DIRS', []),
                'force_ssl': 'no' if options['dont_force_ssl'] else 'yes',
            },
            'roles': [
                'base',
                'swap',
                'opensmtpd',
                'postgres',
                'nginx',
                'django',
                'ssl',
                'ownership',
                'ufw',
            ]
        }]

        if hasattr(settings, 'UP_EXTRAS'):
            # available extras: redis, memcached, phantomjs, kronos
            yam[0]['roles'].extend(getattr(settings, 'UP_EXTRAS'))
            print(yam[0]['roles'])

        if hasattr(settings, 'UP_VARS'):
            for k, val in getattr(settings, 'UP_VARS', {}).items():
                yam[0]['vars'][k] = val
                print('{}: {}'.format(k, val))

        app_yml = open(os.path.join(up_dir, '{}.yml'.format(app_name)), 'w')
        yaml.dump(yam, app_yml)

        # create the hosts file for ansible
        with open(os.path.join(up_dir, 'hosts'), 'w') as hosts_file:
            hosts_file.write('[{}]\n'.format(app_name))
            hosts_file.write('\n'.join(hostnames))

        extra = []
        tags = []

        if options['ssl']:
            tags.append('ssl')

        if options['quick']:
            tags.append('deploy')

        if tags:
            extra.append('-t')
            extra.append(','.join(tags))

        if options['verbose']:
            extra.append('-vvvv')

        # first execute just the `init` tag to ensure Python 2.7 is available (only if not in quick mode)
        if not options['quick']:
            yam[0]['gather_facts'] = 'no'
            app_yml_no_facts = open(os.path.join(up_dir, '{}-nofacts.yml'.format(app_name)), 'w')
            yaml.dump(yam, app_yml_no_facts)
            init_command = ['ansible-playbook', '-i', os.path.join(up_dir, 'hosts')]
            init_command.extend(['-t', 'init'])
            init_command.extend([os.path.join(up_dir, '{}-nofacts.yml'.format(app_name))])
            subprocess.call(init_command)

        # build the ansible command
        command = ['ansible-playbook', '-i', os.path.join(up_dir, 'hosts')]
        command.extend(extra)
        command.extend([os.path.join(up_dir, '{}.yml'.format(app_name))])

        # execute ansible
        return_code = subprocess.call(command)

        # mark as released on opbeat!
        if hasattr(settings, 'OPBEAT') and return_code == 0:
            op_id = settings.OPBEAT['ORGANIZATION_ID']
            app_id = settings.OPBEAT['APP_ID']
            rev = subprocess.getoutput("git log -n 1 --pretty=format:%H")

            requests.post('https://intake.opbeat.com/api/v1/organizations/{}/apps/{}/releases/'.format(op_id, app_id), {
                'rev': rev,
                'status': 'completed',
            }, headers={'Authorization': 'Bearer {}'.format(settings.OPBEAT['SECRET_TOKEN'])})
