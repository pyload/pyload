#!/usr/bin/env bash

# download aia.py from https://github.com/danilobellini/aia/pull/3

set -x

cd "$(dirname "$0")"

wget -N https://github.com/milahu/python-aia/raw/use-cryptography-module/aia.py
