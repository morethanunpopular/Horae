import json
import setuptools

PACKAGE_NAME = "horae"

setuptools.setup(
    name=PACKAGE_NAME,
    version='0.0.0',
    description="CLI tool for submitting jobs to Horae",
    url="https://github.com/morethanunpopular/horae",
    author="Grant Campbell",
    author_email="stars.salvage.man@gmail.com",
    packages=setuptools.find_packages(),
    entry_points = {
       "console_scripts": ["hrun=horae:hrun_cli"]
    }
)

