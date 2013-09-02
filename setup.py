from setuptools import setup

version = '0.18dev'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('TODO.rst').read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    'Django',
    'django-extensions',
    'django-nose',
    'pkginfo',
    'Pillow',
    'matplotlib',
    'pandas',
    'numpy',
    'scipy',
    'south',
    'netCDF4',
    'xlwt',
    'pyproj', # apparantly Lizard implicitly depends on this
    'ordereddict', # netCDF4 needs this in Python 2.6
    'psycopg2',
    ],

tests_require = [
    ]

setup(name='lizard-kml',
      version=version,
      description="Keyhole Markup Language support for Lizard using the Google Earth plugin.",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Programming Language :: Python',
                   'Framework :: Django',
                   ],
      keywords=[],
      author='Fedor Baart; Erik-Jan Vos',
      author_email='erikjan.vos@nelen-schuurmans.nl',
      url='http://nelen-schuurmans.nl/',
      license='GPL',
      packages=['lizard_kml'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require = {'test': tests_require},
      entry_points={
          'console_scripts': [
          ]},
      )
