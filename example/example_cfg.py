# MREST app configuration
PUBLIC_NAME = 'Coin collection'
SA_ENGINE_URL = 'sqlite:///:memory:'

# require authentication by default?
DEFAULT_AUTH = True

# Routes always expected to be private.
# Don't allow unauthenticated requests even if no pub_key is registered and default_auth is True.
# Example: {'coin':['PUT']} will tell the client to always authenticate PUT requests to the coin model.
PRIVATE_ROUTES = {}

# Routes always expected to be public. Don't require auth, even if default_auth is True.
# Example: {'coin':['GET']} will tell the client to never authenticate GET requests to the coin model.
PUBLIC_ROUTES = {}

# Add authentication details (ECC curve and pub key). Values will be ignored if no auth routes are specified.
ECC_CURVE = 'SECP256k1'  # currently only SECP256k1 is supported
ECC_PRIV_KEY = """
-----BEGIN EC PRIVATE KEY-----
MHQCAQEEICjIzBW8J5kdNu0aHN11N6NgWQ9D8YB4S8EppLbX5+sBoAcGBSuBBAAK
oUQDQgAE31O8+NaE+QS6ehXbXkPdN62rW1/vV1dB2/UhgV4/c47FhaIiINOuKka1
rb93dmsIJhAjdh54PICjdvSF2EKdVQ==
-----END EC PRIVATE KEY-----
"""

# if True, all responses will be signed using the key above
SIGN_RESPONSES = True

# optionally add models as configuration parameters
MODELS = {}

# Logging configuration
LOG_DIR = "./"
LOG_NAME = 'MREST-app.log'
USE_GELF = False