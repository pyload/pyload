#!/bin/sh

BASE_URL="https://raw.githubusercontent.com/GammaC0de/pycurl-win-mirror/master/"
case "$1" in
  "3.6")
    WHEEL_FILE="pycurl-7.43.0.4-cp36-cp36m-win_amd64.whl"
    ;;
  "3.7")
    WHEEL_FILE="pycurl-7.45.1-cp37-cp37m-win_amd64.whl"
    ;;
  "3.8")
    WHEEL_FILE="pycurl-7.45.1-cp38-cp38-win_amd64.whl"
    ;;
  "3.9")
    WHEEL_FILE="pycurl-7.45.1-cp39-cp39-win_amd64.whl"
    ;;
  "3.10")
    WHEEL_FILE="pycurl-7.45.1-cp310-cp310-win_amd64.whl"
    ;;
  "3.11")
    WHEEL_FILE="pycurl-7.45.1-cp311-cp311-win_amd64.whl"
    ;;
  "3.12")
    WHEEL_FILE="pycurl-7.45.2-cp312-cp312-win_amd64.whl"
    ;;
  *)
    echo "::error::Unsupported Python version"
    exit 1
    ;;
esac

pip install "${BASE_URL}${WHEEL_FILE}"
exit 0
