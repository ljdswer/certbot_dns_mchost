#!/bin/sh

certbot certonly \
    --non-interactive \
    --preferred-challenges dns \
    --authenticator dns-mchost \
    --dns-mchost-credentials /.env \
    $@
