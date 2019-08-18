import os
# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = # create a key with eg 'openssl rand -base64 32', one may also put it directly here

# Default is to only accept connections from localhost.
# If you feel save and you're behind a proxy, use ALLOWED_HOSTS = ["*"] to allow connections from everywhere.
# ALLOWED_HOSTS = []

# The ACC server exe, in case of linux, wine is used to execute the binary
WINE_PATH = os.getenv('WINE_PATH', 'wine')                          # defaults to 'wine', windows: just set to empty string ""
ACC_SERVER_PATH = os.getenv('ACC_SERVER_PATH', 'accServer.exe')     # defaults to 'accServer.exe'
ACCEXEC = [i for i in [WINE_PATH, ACC_SERVER_PATH] if i]            # Omit WINE_PATH if empty

ACCSERVER = os.getenv('ACCSERVER', '/server')                       # defaults to '/server', windows: 'C:\\PATH\\TO\\ACC\\server'

# Directory where configs and instances are placed
# (docker: this folder is mounted from the host via a docker volume)
DATA_DIR = os.getenv('DATA_DIR', '/data')                           # defaults to /data, s.t. like '/tmp/accserver-data' or 'C:\\Users\\someuser\\accserver-data'
CONFIGS = os.path.join(DATA_DIR, 'configs')
INSTANCES = os.path.join(DATA_DIR, 'instances')
