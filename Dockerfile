# Highly-Optimized Docker Image of pyLoad (ubuntu variant)
# AUTHOR: vuolter
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

ARG UBUNTU_RELEASE="bionic"




FROM lsiobase/ubuntu:$UBUNTU_RELEASE as builder

ARG APT_INSTALL_OPTIONS="--no-install-recommends --yes"
ARG PIP_INSTALL_OPTIONS="--disable-pip-version-check --no-cache-dir --no-compile --upgrade"

ARG APK_PACKAGES="python3 openssl python3-distutils wget"
ARG PIP_PACKAGES="pip setuptools wheel"

RUN \
echo "**** install Python ****" && \
apt-get update && apt-get install $APT_INSTALL_OPTIONS $APK_PACKAGES && \
ln -sf python3 /usr/bin/python && \
\
echo "**** install pip ****" && \
wget -q -O - "https://bootstrap.pypa.io/get-pip.py" | python /dev/stdin $PIP_INSTALL_OPTIONS && \
ln -sf pip3 /usr/bin/pip




FROM builder as wheels_builder

COPY setup.cfg /source/setup.cfg
WORKDIR /wheels

RUN \
echo "**** build pyLoad dependencies ****" && \
python -c "import configparser as cp; c = cp.ConfigParser(); c.read('/source/setup.cfg'); print(c['options']['install_requires'] + c['options.extras_require']['extra'])" | \
xargs pip wheel --wheel-dir=.




FROM builder as source_builder

COPY . /source
WORKDIR /source

ARG PIP_INSTALL_OPTIONS="--disable-pip-version-check --no-cache-dir --no-compile --upgrade"
ARG PIP_PACKAGES="Babel Jinja2"

RUN \
echo "**** build pyLoad locales ****" && \
pip install $PIP_INSTALL_OPTIONS $PIP_PACKAGES && \
python setup.py build_locale




FROM builder as package_builder

COPY --from=wheels_builder /wheels /wheels
COPY --from=source_builder /source /source
WORKDIR /package

ARG PIP_INSTALL_OPTIONS="--disable-pip-version-check --no-cache-dir --no-compile --upgrade"

RUN \
echo "**** build pyLoad package ****" && \
pip install $PIP_INSTALL_OPTIONS --find-links=/wheels --no-index --prefix=. /source[extra]




FROM builder

LABEL \
version="1.0" \
description="The free and open-source Download Manager written in pure Python" \
maintainer="vuolter@gmail.com"

# Set Python to force stdin, stdout and stderr to be totally unbuffered.
ENV PYTHONUNBUFFERED=1

# Stop if any script (fix-attrs or cont-init) has failed.
ENV S6_BEHAVIOUR_IF_STAGE2_FAILS=2

ARG APT_INSTALL_OPTIONS="--no-install-recommends --yes"
ARG APT_PACKAGES="sqlite tesseract-ocr unrar"

ARG TEMP_PATHS="/root/.cache /tmp/* /var/lib/apt/lists/* /var/tmp/*"

RUN \
echo "**** install binary packages ****" && \
apt-get install $APT_INSTALL_OPTIONS $APT_PACKAGES && \
\
echo "**** create s6 fix-attr script ****" && \
echo -e "/config true abc 0644 0755\n \
/downloads false abc 0644 0755" > /etc/fix-attrs.d/10-run && \
\
echo "**** create s6 service script ****" && \
mkdir -p /etc/services.d/pyload && \
echo -e "#!/usr/bin/with-contenv bash\n\n \
umask 022\n \
exec s6-setuidgid abc pyload --userdir /config --storagedir /downloads" > /etc/services.d/pyload/run && \
\
echo "**** cleanup ****" && \
rm -rf $TEMP_PATHS && \
\
echo "**** finalize pyLoad ****"

COPY --from=package_builder /package /usr/local

EXPOSE 8001 9666

VOLUME /config /downloads
