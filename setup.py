#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017, 2022 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

from setuptools import setup


setup(
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
)
