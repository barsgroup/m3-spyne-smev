import os
from distutils.core import setup


def read_file(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as fd:
        return fd.read()

setup(
    name="spyne-smev",
    version="0.1.4",
    packages=[
        "spyne_smev", "spyne_smev.smev256", "spyne_smev.smev255",
        "spyne_smev.server", "spyne_smev.wsse"],
    package_dir={"": "src"},
    package_data={"": ["xsd/*"]},
    url="http://bitbucket.org/bars-group/spyne-smev",
    license=read_file("LICENSE"),
    description=read_file("DESCRIPTION"),
    author="Timur Salyakhutdinov",
    author_email="t.salyakhutdinov@gmail.com",
    install_requires=read_file("REQUIREMENTS")
)

