import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="skilletlib",
    version="0.0.1",
    author="Nathan Embery",
    author_email="nembery@paloaltonetworks.com",
    description="Tools for working with PAN-OS Skillets in Python 3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nembery/skilletlib",
    packages=setuptools.find_packages(),
    install_requires=[
        "oyaml",
        "pan-python",
        "pathlib",
        "jinja2",
        "pyyaml",
        "xmldiff",
        "xmltodict",
        "request-toolbelt",
        "requests",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache 2.0",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)