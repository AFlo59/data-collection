from setuptools import setup, find_packages

setup(
    name="data-collection",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "selenium",
        "python-dotenv",
        "playwright",
    ],
) 