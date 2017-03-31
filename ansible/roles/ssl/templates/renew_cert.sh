#!/usr/bin/env sh
set -e
python /var/www/{{ app_name }}/acme-tiny/acme_tiny.py --account-key /var/certs/account.key --csr /var/certs/{{ app_name }}.csr --acme-dir /var/www/challenges/ > /tmp/signed-{{ app_name }}.crt || exit
wget -O - https://letsencrypt.org/certs/lets-encrypt-x3-cross-signed.pem > intermediate-{{ app_name }}.pem
cat /tmp/signed-{{ app_name }}.crt intermediate-{{ app_name }}.pem > /var/certs/{{ app_name }}.chained.pem
systemctl reload nginx