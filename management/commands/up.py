from __future__ import print_function

import os
import random
import shutil
import string
import subprocess
import sys
import tempfile

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string


"""
Deploying Django applications as quickly as you create them

Usage:
    ./manage.py up <hostname>... [--debug] [--skip-base] [--verbose]
"""


class Command(BaseCommand):
    help = "Deploy your Django site to a remote server"

    def add_arguments(self, parser):
        parser.add_argument("hostnames", nargs="+", type=str)
        parser.add_argument("--domain", nargs=1, type=str)
        parser.add_argument("--debug", action="store_true", default=False, dest="debug")
        parser.add_argument("--skip-base", action="store_true", default=False, dest="skip_base")
        parser.add_argument(
            "--verbose", action="store_true", default=False, dest="verbose"
        )

    def handle(self, *args, **options):
        ansible_dir = os.path.join(os.path.dirname(__file__), "..", "..", "ansible")
        hostnames = options["hostnames"]
        app_name = settings.WSGI_APPLICATION.split(".")[0]

        up_dir = tempfile.TemporaryDirectory().name + "/django_up"
        app_tar = tempfile.NamedTemporaryFile(suffix=".tar")

        # copy our ansible files into our up_dir
        shutil.copytree(ansible_dir, up_dir)

        # Build up the django_environment variable from the contents of the .env
        # file on the local machine. These environment variables are injected into
        # the running environment using the app.sh file that's created.
        django_environment = {}
        try:
            with open(os.path.join(settings.BASE_DIR, ".env")) as env_file:
                for line in env_file.readlines():
                    if line and "=" in line and line.strip()[0] not in ["#", ";"]:
                        var, val = line.split("=", 1)
                        if " " not in var:
                            django_environment[var] = val.strip()
                        else:
                            print("Ignoring environment variable with space: ", line)
            print("Loaded environment from .env: ", django_environment.keys())
        except FileNotFoundError:
            pass

        # create a tarball of our application code, excluding some common directories
        # and files that are unlikely to be wanted on the remote machine
        subprocess.call(
            [
                "tar",
                "--exclude",
                "*.pyc",
                "--exclude",
                ".git",
                "--exclude",
                "*.sqlite3",
                "--exclude",
                "__pycache__",
                "--exclude",
                "*.log",
                "--exclude",
                "{}.tar".format(app_name),
                "--dereference",
                "-cf",
                app_tar.name,
                ".",
            ]
        )

        # use allowed_hosts to set up our domain names
        domains = []

        if options["domain"]:
            domains = options["domain"]
        else:
            for host in settings.ALLOWED_HOSTS:
                if host.startswith("."):
                    domains.append("*" + host)
                elif "." in host and not host.startswith("127."):
                    domains.append(host)

        for h in hostnames:
            if h not in domains:
                sys.exit(
                    "{} isn't in allowed domains or DJANGO_ALLOWED_HOSTS".format(h)
                )

        # create a random database password to use for the database user, this is
        # saved on the remote machine and will be overridden by the ansible run
        # if it exists
        db_pass = str(get_random_string(12, string.ascii_letters + string.digits))

        yam = [
            {
                "hosts": app_name,
                "remote_user": "root",
                "gather_facts": "yes",
                "vars": {
                    "app_name": app_name,
                    "service_name": app_name.replace("_", ""),
                    "domain_names": " ".join(domains),
                    "gunicorn_port": getattr(settings, "GUNICORN_PORT", "9000"),
                    "app_tar": app_tar.name,
                    "python_version": getattr(
                        settings, "UP_PYTHON_VERSION", "python3.8"
                    ),
                    "db_password": db_pass,
                    "django_debug": "yes" if options["debug"] else "no",
                    "django_environment": django_environment,
                    "extra_app_dirs": getattr(settings, "UP_DIRS", []),
                    "certbot_domains": "-d " + " -d ".join(domains),
                    "certbot_email": "brenton@brntn.me",
                    "domain": domains[0],
                },
                "roles": [
                    "base",
                    "ufw",
                    "opensmtpd",
                    "postgres",
                    "nginx",
                    "django",
                    "ownership",
                ],
            }
        ]

        # if --skip-base is provided we remove "base" roles from the run
        # this requires that these have been previously ran (i.e. you cannot)
        # use the flag on the first run.
        if options["skip_base"]:
            yam[0]["roles"].remove("base")
            yam[0]["roles"].remove("ufw")
            yam[0]["roles"].remove("opensmtpd")

        #
        app_yml = open(os.path.join(up_dir, "{}.yml".format(app_name)), "w")
        yaml.dump(yam, app_yml)

        # create the hosts file for ansible
        with open(os.path.join(up_dir, "hosts"), "w") as hosts_file:
            hosts_file.write("[{}]\n".format(app_name))
            hosts_file.write("\n".join(hostnames))

        # add any extra ansible arguments that we need
        ansible_args = []
        if options["verbose"]:
            ansible_args.append("-vvvv")

        # build the ansible command
        command = ["ansible-playbook", "-i", os.path.join(up_dir, "hosts")]
        command.extend(ansible_args)
        command.extend([os.path.join(up_dir, "{}.yml".format(app_name))])

        # execute ansible
        return_code = subprocess.call(command)
        sys.exit(return_code)
