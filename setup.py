import os
import re
import sys
from collections import defaultdict

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version(*file_paths):
    """Retrieves the version from django_pint_field/__init__.py"""
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


def get_extras_require(path, add_all=True):
    # https://hanxiao.io/2019/11/07/A-Better-Practice-for-Managing-extras-require-Dependencies-in-Python/
    with open(path) as fp:
        extra_deps = defaultdict(set)
        for k in fp:
            if k.strip() and not k.startswith("#"):
                tags = set()
                if ":" in k:
                    k, v = k.split(":")
                    tags.update(vv.strip() for vv in v.split(","))
                tags.add(re.split("[<=>]", k)[0])
                for t in tags:
                    extra_deps[t].add(k)

        # add tag `all` at the end
        if add_all:
            extra_deps["all"] = set(vv for v in extra_deps.values() for vv in v)

    return extra_deps


readme = open("README.md").read()
#changelog = open("CHANGELOG.md").read()
requirements = open("requirements/base.txt").readlines()
#extras_requirements_path = "requirements/extras.txt"
#version = get_version("django_pint_field", "__init__.py")
version = 1

if sys.argv[-1] == "publish":
    try:
        import wheel

        print("Wheel version: ", wheel.__version__)
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system("python setup.py sdist upload")
    os.system("python setup.py bdist_wheel upload")
    sys.exit()

if sys.argv[-1] == "tag":
    print("Tagging the version on git:")
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()

classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Operating System :: OS Independent",
    "Topic :: Software Development :: Libraries",
    "Topic :: Database",
    "Topic :: Utilities",
    "Environment :: Web Environment",
    "Framework :: Django",
    "Framework :: Django :: 3.2",
    "Framework :: Django :: 4.0",
    "Framework :: Django :: 4.1",
]

setup(
    name="django-pint-field",
    version=version,
    description="""Use pint with Django's ORM""",
    long_description=readme, # + "\n\n" + changelog,
    long_description_content_type="text/markdown",
    author="Jack Linke",
    author_email="jack@watervize.com",
    license="MIT",
    url="https://github.com/jacklinke/django-pint-field/",
    project_urls={
        "Documentation": "https://django-pint-field.readthedocs.io/en/latest/",
        "Source": "https://github.com/jacklinke/django-pint-field/",
        "Tracker": "https://github.com/jacklinke/django-pint-field/issues",
    },
    packages=[
        "django_pint_field",
    ],
    package_dir={"django_pint_field": "django_pint_field"},
    include_package_data=True,
    keywords="django-pint-field, quantity, unit, magnitude, measurement",
    python_requires=">=3.8, <4",
    classifiers=classifiers,
    install_requires=requirements,
    #extras_require=get_extras_require(extras_requirements_path),
)
