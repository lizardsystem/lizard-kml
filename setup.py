from setuptools import setup

version = '0.4dev'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('TODO.rst').read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    'Django == 1.4',
    'django-extensions',
    'django-nose',
    'lizard-ui >= 3.0',
    'pkginfo',
    'PIL',
    'matplotlib',
    'numpy',
    'scipy',
    'netCDF4 >= 1.0, < 2.0',
    'xlwt >= 0.7.4, < 0.8',
    'django-tastypie >= 0.9.11, < 1.0',
    'djangorestframework >= 0.3.3, < 0.4'
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
