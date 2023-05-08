from setuptools import setup, find_packages
import os

# Read the contents of the README.md file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='embeddings-util',
    version='1.0.1',
    description='The embeddings package is a utility for generating question-answer pairs and embeddings from HTML pages or text input. It utilizes the OpenAI API to generate question-answer pairs and embeddings. This package is useful for generating training data for chatbots or question-answering models.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Osiris Development LLC',
    author_email='support@pagepixels.com',
    url='https://github.com/ChatClue/embedding-python',
    packages=find_packages(),
    install_requires=[
        'requests',
        'screenshots_pagepixels',
        'bs4'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
