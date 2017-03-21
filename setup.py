# -*- coding: utf-8 -*-
from distutils.core import setup


requires = []
with open('REQUIREMENTS', 'r') as f:
    requires.extend(f.readlines())

setup(
    name="m3-spyne-smev",
    version="0.1.12",
    url="http://bitbucket.org/bars-group/spyne-smev",
    license='MIT',
    author='BARS Group',
    description=u'Набор протоколов фреймворка spyne для работы со СМЭВ',
    author_email='bars@bars-open.ru',
    package_dir={"": "src"},
    packages=[
        "spyne_smev", "spyne_smev.smev256", "spyne_smev.smev255",
        "spyne_smev.server", "spyne_smev.wsse"],
    package_data={"": ["xsd/*"]},
    install_requires=requires,
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Natural Language :: Russian',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 5 - Production/Stable',
    ],
)
