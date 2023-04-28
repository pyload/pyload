# Highly-Optimized Docker Image of pyLoad (alpine variant)
#       ____________
#   ___/       |    \_____________ _                 _ ___
#  /        ___/    |    _ __ _  _| |   ___  __ _ __| |   \
# /    \___/  ______/   | '_ \ || | |__/ _ \/ _` / _` |    \
# \            ◯ |      | .__/\_, |____\___/\__,_\__,_|    /
#  \_______\    /_______|_|   |__/________________________/
#           \  /
#            \/

ARG IMAGE_TAG="3.16"
ARG IMAGE_CREATED
ARG IMAGE_AUTHORS="Walter Purcaro <vuolter@gmail.com>"
ARG IMAGE_URL="https://github.com/pyload/pyload"
ARG IMAGE_DOCUMENTATION="https://github.com/pyload/pyload/blob/main/README.md"
ARG IMAGE_SOURCE="https://github.com/pyload/pyload/blob/main/Dockerfile.alpine"
ARG IMAGE_VERSION="2.0.0"
ARG IMAGE_REVISION
ARG IMAGE_VENDOR="pyload"
ARG IMAGE_LICENSES="ISC"
ARG IMAGE_TITLE="pyLoad"
ARG IMAGE_DESCRIPTION="The free and open-source Download Manager written in pure Python"


ARG APK_INSTALL_OPTIONS="--no-cache"
ARG PIP_INSTALL_OPTIONS="--disable-pip-version-check --no-cache-dir --no-compile --upgrade"


FROM lsiobase/alpine:$IMAGE_TAG AS builder

ARG APK_PACKAGES="curl-dev ffmpeg openssl p7zip python3 sqlite tesseract-ocr"
ARG PIP_PACKAGES="pip setuptools wheel"

RUN echo "**** install binary packages ****" && \
    apk add $APK_INSTALL_OPTIONS $APK_PACKAGES && \
    \
    echo "**** install pip packages ****" && \
    python3 -m ensurepip && \
    rm -rf /usr/lib/python*/ensurepip && \
    pip3 install $PIP_INSTALL_OPTIONS $PIP_PACKAGES


FROM builder AS wheels_builder

ARG APK_PACKAGES="gcc g++ musl-dev python3-dev libffi-dev openssl-dev jpeg-dev zlib-dev libxml2-dev libxslt-dev cargo"

ENV PYCURL_SSL_LIBRARY="openssl"

COPY . /source
WORKDIR /wheels

RUN echo "**** install build packages ****" && \
    apk add $APK_INSTALL_OPTIONS $APK_PACKAGES && \
    \
    echo "**** build pyLoad dependencies ****" && \
    pip3 wheel -w /wheels /source


FROM builder AS source_builder

ARG PIP_PACKAGES="Babel Jinja2"

COPY . /source
WORKDIR /source

RUN echo "**** build pyLoad locales ****" && \
    pip3 install $PIP_INSTALL_OPTIONS $PIP_PACKAGES && \
    python3 setup.py build_locale


FROM builder AS package_builder

COPY --from=wheels_builder /wheels /wheels
COPY --from=source_builder /source /source
WORKDIR /package

RUN echo "**** build pyLoad package ****" && \
    pip3 install $PIP_INSTALL_OPTIONS --find-links=/wheels --no-index --prefix=. /source[extra]


FROM builder

# Set Python to force stdin, stdout and stderr to be totally unbuffered.
ENV PYTHONUNBUFFERED="1"

# Stop if any script (fix-attrs or cont-init) has failed.
ENV S6_BEHAVIOUR_IF_STAGE2_FAILS="2"

# Set Python to use UTF-8 encoding rather than ASCII.
ENV LANG="C.UTF-8"

ARG TEMPDIR="/root/.cache /tmp/* /var/tmp/*"

RUN echo "**** create s6 service script ****" && \
    mkdir -p /etc/services.d/pyload && \
    echo -e "#!/usr/bin/with-contenv bash\n\n \
    umask 022\n \
    export PYTHONPATH=\$PYTHONPATH:/usr/local/lib/python3.10/site-packages\n \
    export HOME=/config\n \
    exec s6-setuidgid abc pyload --userdir /config --storagedir /downloads" > /etc/services.d/pyload/run && \
    \
    echo "**** cleanup ****" && \
    rm -rf $TEMPDIR && \
    \
    echo "**** finalize ****"

COPY --from=package_builder /package /usr/local

EXPOSE 8000 9666

VOLUME /config /downloads

LABEL org.opencontainers.image.created=$IMAGE_CREATED
LABEL org.opencontainers.image.authors=$IMAGE_AUTHORS
LABEL org.opencontainers.image.url=$IMAGE_URL
LABEL org.opencontainers.image.documentation=$IMAGE_DOCUMENTATION
LABEL org.opencontainers.image.source=$IMAGE_SOURCE
LABEL org.opencontainers.image.version=$IMAGE_VERSION
LABEL org.opencontainers.image.revision=$IMAGE_REVISION
LABEL org.opencontainers.image.vendor=$IMAGE_VENDOR
LABEL org.opencontainers.image.licenses=$IMAGE_LICENSES
LABEL org.opencontainers.image.title=$IMAGE_TITLE
LABEL org.opencontainers.image.description=$IMAGE_DESCRIPTION
