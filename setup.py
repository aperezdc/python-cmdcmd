#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

from setuptools import setup, find_packages
from os import path


def distrib_file(*relpath):
    try:
        return open(path.join(path.dirname(__file__), *relpath), "rU",
                    encoding="utf-8")
    except IOError:
        class DummyFile(object):
            def read(self):
                return ""
        return DummyFile()


def get_version():
    for line in distrib_file("cmdcmd", "__init__.py"):
        if line.startswith("__version__"):
            line = line.split()
            if line[0] == "__version__":
                return line[2].strip()
    return None


def get_readme():
    return distrib_file("README.rst").read()


setup(
    name="cmdcmd",
    version=get_version(),
    description="Ergonomic command line interface maker",
    long_description=get_readme(),
    author="Adrian Perez de Castro",
    author_email="aperez@igalia.com",
    url="https://github.com/aperezdc/python-cmdcmd",
    packages=find_packages(),
    extras_require={
        "dev": [
            # Please keep in alphabetical order.
            "coverage",
            "flake8-author",
            "flake8-builtins",
            "flake8-comprehensions",
            "flake8-debugger",
            "flake8-deprecated",
            "flake8-diff",
            "flake8-dodgy",
            "flake8-double-quotes",
            "flake8-pep3101",
            "flake8-tuple",
            "green",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3 :: Only",
    ]
)
