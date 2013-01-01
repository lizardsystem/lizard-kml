import os

import logging
# Set up logging here so we can log in the settings module.
# After initialization, Django's LOGGING settings are used.
logging.basicConfig(
    format='%(asctime)s %(module)s %(message)s',
    level=logging.DEBUG
)

from lizard_ui.settingshelper import setup_logging

logger = logging.getLogger(__name__)

DEBUG = True
TEMPLATE_DEBUG = True

# Set matplotlib defaults.
# Import specific matplotlib settings for this app.
from lizard_kml.jarkus.matplotlib_settings import set_matplotlib_defaults
set_matplotlib_defaults()

# SETTINGS_DIR allows media paths and so to be relative to this settings file
# instead of hardcoded to c:\only\on\my\computer.
SETTINGS_DIR = os.path.dirname(os.path.realpath(__file__))

# BUILDOUT_DIR is for access to the "surrounding" buildout, for instance for
# BUILDOUT_DIR/var/static files to give django-staticfiles a proper place
# to place all collected static files.
BUILDOUT_DIR = os.path.abspath(os.path.join(SETTINGS_DIR, '..'))
LOGGING = setup_logging(BUILDOUT_DIR)

# ENGINE: 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
# In case of geodatabase, prepend with:
# django.contrib.gis.db.backends.(postgis)
DATABASES = {
    # If you want to use another database, consider putting the database
    # settings in localsettings.py. Otherwise, if you change the settings in
    # the current file and commit them to the repository, other developers will
    # also use these settings whether they have that database or not.
    # One of those other developers is Jenkins, our continuous integration
    # solution. Jenkins can only run the tests of the current application when
    # the specified database exists. When the tests cannot run, Jenkins sees
    # that as an error.
    'default': {
        'NAME': os.path.join(BUILDOUT_DIR, 'var', 'sqlite', 'test.db'),
        'ENGINE': 'django.db.backends.sqlite3',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',  # empty string for localhost.
        'PORT': '',  # empty string for default.
        }
    }
SITE_ID = 1
INSTALLED_APPS = [
    'lizard_kml',
    'lizard_ui',
    'compressor',
    'south',
    'django_nose',
    'django_extensions',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.gis',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    ]
ROOT_URLCONF = 'lizard_kml.urls'

TEMPLATE_CONTEXT_PROCESSORS = (
    # Uncomment this one if you use lizard-map.
    # 'lizard_map.context_processors.processor.processor',
    # Default django 1.3 processors.
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages"
    )

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BUILDOUT_DIR, 'var', 'cache'),
    }
}

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ['--with-doctest', '--verbosity=3']
SOUTH_TESTS_MIGRATE = False # To disable migrations and use syncdb instead
SKIP_SOUTH_TESTS = True # To disable South's own unit tests

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'nl-NL'
# For at-runtime language switching.  Note: they're shown in reverse order in
# the interface!
LANGUAGES = [
#    ('en', 'English'),
    ('nl', 'Nederlands'),
]
# If you set this to False, Django will make some optimizations so as not to
# load the internationalization machinery.
USE_I18N = True
LOCALE_PATHS = (os.path.join(SETTINGS_DIR, 'locale'),)

SECRET_KEY = 'testsettings'

# Used for django-staticfiles (and for media files)
STATIC_URL = '/static_media/'
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BUILDOUT_DIR, 'var', 'static')
MEDIA_ROOT = os.path.join(BUILDOUT_DIR, 'var', 'media')
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

LIZARD_KML_STANDALONE = True

# NetCDF databases containing transect (coastal) data, for example.
# Local copies are highly recommended:
# wget "http://opendap.deltares.nl/thredds/fileServer/opendap/rijkswaterstaat/jarkus/profiles/transect.nc"
NC_RESOURCE_LOCAL_DIR = os.path.join(BUILDOUT_DIR, 'var', 'netcdf')

# by default, just use the remote versions
NC_RESOURCE = {
    'transect': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/jarkus/profiles/transect.nc',
    # Use this if we break the deltares server:
    #'transect': 'http://opendap.tudelft.nl/thredds/dodsC/data2/deltares/rijkswaterstaat/jarkus/profiles/transect.nc',
    'BKL_TKL_TND': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/BKL_TKL_MKL/BKL_TKL_TND.nc',
    'DF': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/DuneFoot/DF.nc',
    'MKL': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/BKL_TKL_MKL/MKL.nc',
    'strandbreedte': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/strandbreedte/strandbreedte.nc',
    'strandlijnen': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/strandlijnen/strandlijnen.nc',
    'suppleties': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/suppleties/suppleties.nc',
}

# when a local copy of the .nc file is provided, use that instead
for key in NC_RESOURCE:
    fn = key + '.nc'
    path = os.path.join(NC_RESOURCE_LOCAL_DIR, fn)
    if os.path.isfile(path):
        logger.info('Using %s', path)
        NC_RESOURCE[key] = path

# other local testsettings
# TODO should move these to local test settings, and send Fedor an email about it :)
if os.getlogin() == 'fedorbaart':
    # fedors mac
    NC_RESOURCE['transect'] = '/Users/fedorbaart/Downloads/transect.nc'
    logger.info('Fedors mac, using %s', NC_RESOURCE['transect'])

try:
    # Import local settings that aren't stored in svn/git.
    from lizard_kml.local_testsettings import *
except ImportError:
    pass
