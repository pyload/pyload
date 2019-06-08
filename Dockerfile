ARG PYTHON_VERSION=3.7

FROM python:${PYTHON_VERSION}-alpine

LABEL version="1.0" \
      description="The free and open-source Download Manager written in pure Python" \
      maintainer="vuolter@gmail.com"

USER 405  #: guest user/group in Alpine Linux

COPY . "/pyload"
WORKDIR "/pyload"

RUN apk add --update --no-cache tesseract-ocr unrar && \
    pip install --no-cache-dir -e .[all] && \
    mkdir -p "/opt/pyload/{config,tmp,downloads}"

VOLUME ["/opt/pyload"]

EXPOSE 8000

ENTRYPOINT ["pyload"]
CMD ["--userdir", "/opt/pyload/config", "--cachedir", "/opt/pyload/tmp", "--storagedir", "/opt/pyload/downloads"]
