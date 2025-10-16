ARG RUNTIME_VERSION=3.1-2
FROM astrocrpublic.azurecr.io/runtime:${RUNTIME_VERSION}
COPY requirements.txt /requirements.txt