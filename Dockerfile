FROM python:3.10-alpine AS builder

WORKDIR /build

COPY requirements.txt .
RUN python -m venv /venv
RUN /venv/bin/pip install -r requirements.txt

COPY pyproject.toml .
COPY certbot_dns_mchost certbot_dns_mchost
RUN /venv/bin/pip install .

FROM python:3.10-alpine AS final
COPY --from=builder /venv /venv
COPY docker_entrypoint.sh /
ENV PATH="/venv/bin:$PATH"
ENTRYPOINT [ "/docker_entrypoint.sh" ]
