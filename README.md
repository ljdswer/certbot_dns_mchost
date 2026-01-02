# Certbot DNS McHost Plugin

Certbot plugin for DNS-01 challenge for McHost (my.mchost.ru).

---

## Usage
The most basic usage is:

```bash
docker run --rm \
  -v [secrets_file]:/.env \
  -v [letsencrypt_directory]:/etc/letsencrypt \
  ljdswer/certbot_dns_mchost:latest \
  -d [domain_1] \
  -d [domain_2] \
  ...
```

The snippet above requests certificates for all specified domains once.

Secrets file should be in the following format:
```.env
dns_mchost_user=[your_username]
dns_mchost_pass=[your_password]
```

*Note: McHost does not support token-based authentication*

This plugin could be used with normal Certbot's autorenewal feature,
with cron or even with docker-compose like this:
```compose.yml
services:
  certbot:
    image: ljdswer/certbot_dns_mchost
    restart: always
    volumes:
      - .env:/.env # Assuming .env is in the same directory as compose.yml
      - /etc/letsencrypt:/etc/letsencrypt
    entrypoint: /bin/sh
    command: >
      -c '
        while true; do
          /docker_entrypoint.sh -d [domain_1] -d [domain_2] -d ...; # Renew certificate if needed
          echo Sleeping for a month;
          sleep 2505600; # 29 days. Certbot only renews a certificate if it has less than 30 days left before expiration, no need to sleep any longer
        done
      '
```
