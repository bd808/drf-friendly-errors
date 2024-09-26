from tox.config import parseconfig
import os

file = open(".travis.yml", "w")
base_python = {
    "py36": "3.6",
    "py37": "3.7",
    "py38": "3.8-dev",
    "lint": "3.7",
    "read": "3.7",
}
env_configs = parseconfig(None, "tox").envconfigs

file.write("dist: xenial" + "\r")
file.write("language: python" + "\r")
file.write("matrix:" + "\r")
file.write("  include:" + "\r")
for env in env_configs:
    file.write("    - python: %s" % base_python[env[0:4]] + "\r")
    file.write("      env: TOX_ENV=%s" % env + "\r")
file.write("install:" + "\r")
file.write(" - pip install tox" + "\r")
file.write("script:" + "\r")
file.write(" - tox -e $TOX_ENV" + "\r")
file.close()
