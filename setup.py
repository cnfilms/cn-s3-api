from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'src/info.py')) as f:
    exec(f.read())

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='cn_s3_api',
    version=__version__,

    description='OVH S3 api',
    long_description=long_description,
    url='https://github.com/cnfilms/cn_s3_api',

    author=__author__,
    author_email='technique@cinego.net',

    license=__license__,

    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],

    keywords='ovh s3 api boto3 client',

    packages=find_packages(exclude=['packaging', 'docs', 'tests']),

    install_requires=[
        'boto3',
    ],

    # 3.6+
    python_requires='>=3.6',
)
