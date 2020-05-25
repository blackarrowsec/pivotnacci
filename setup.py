import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

name = "pivotnacci"

setuptools.setup(
    name=name,
    version="0.0.2",
    author="Eloy Perez",
    author_email="eloy.perez@tarlogic.com",
    description="A tool to make socks connections through HTTP agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/blackarrowsec/" + name,
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    scripts=[name],
)
