from config.dev import *

TESTING = True

ZODB_STORAGE = 'memory://'

# Unnecessary to specify here, but it fills out the coverage
STATIC_ROOT = 'http://127.0.0.1/'

CSRF_ENABLED = False

BCRYPT_LOG_ROUNDS = 1
