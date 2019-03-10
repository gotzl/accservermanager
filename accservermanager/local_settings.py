import os
# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = # create a key with eg 'openssl rand -base64 32', one may also put it directly here

# Default is to only accept connections from localhost.
# If you feel save and you're behind a proxy, use ALLOWED_HOSTS = ["*"] to allow connections from everywhere.
# ALLOWED_HOSTS = []

# The ACC server exe, in case of linux, wine is used to execute the binary
ACCEXEC = ['wine','accServer.exe']      # windows: just set it to 'accServer.exe' (no list!)
ACCSERVER = '/tmp/server'                   # windows: 'C:\\PATH\\TO\\ACC\\server'

# Directory where configs and instances are placed (docker: this is mounted from the host via a docker volume)
DATA_DIR = '/tmp/data'                      # s.t. like '/tmp/accserver-data' or 'C:\\Users\\someuser\\accserver-data'
CONFIGS = os.path.join(DATA_DIR, 'configs')
INSTANCES = os.path.join(DATA_DIR, 'instances')