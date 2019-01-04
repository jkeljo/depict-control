from codecs import open
from os import path
from setuptools import setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="depict-control",
    version="1.0",
    description="Control your Depict digital art frames "
                "(depict.com)",
    long_description=long_description,
    url="https://github.com/jkeljo/depict-control",
    author="Jonathan Keljo",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Home Automation",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
    ],
    keywords="depict",
    packages=["depict_control"],
    install_requires=[
        "aiohttp",
        "netifaces",
    ],
    python_requires=">=3.5.1",
)
