from distutils.core import setup

VERSION = '0.3'

classifiers = [
    "Intended Audience :: Developers",
    "Programming Language :: Python",
    "Operating System :: OS Independent",
    "Topic :: Software Development :: Libraries",
    "Environment :: Web Environment",
    "Framework :: Django",
]

setup(
    name='django-navigation',
    version=VERSION,
    url='https://github.com/Threespot/django-navigation',
    author='Chuck Harmston',
    author_email='chuck.harmston@threespot.com',
    packages=['navigation'],
    package_dir={'navigation': 'navigation'},
    description=(
        'Provides a robust system for creating arbitrary menus with '
        'django-pagemanager.'
    ),
    classifiers=classifiers,
    install_requires=[
        'django>=1.3',
        'django-mptt>=0.4.2',
        'django-pagemanager>=0.1',
    ],
)

