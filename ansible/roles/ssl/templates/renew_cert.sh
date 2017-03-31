#!/usr/bin/env sh
set -e
python /var/www/{{ app_name }}/acme-tiny/acme_tiny.py --account-key /var/certs/account.key --csr /var/certs/{{ app_name }}.csr --acme-dir /var/www/challenges/ > /tmp/signed.crt || exit
wget -O - https://letsencrypt.org/certs/lets-encrypt-x3-cross-signed.pem > intermediate.pem
cat /tmp/signed.crt intermediate.pem > /var/certs/{{ app_name }}.chained.pem
nginx -s reload
