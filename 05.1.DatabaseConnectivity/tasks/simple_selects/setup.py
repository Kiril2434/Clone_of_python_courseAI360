from setuptools import setup

# TODO: rewrite me using pyproject.toml

packages = {
    'simple_selects': './'
}

setup(
    name="simple_selects",
    version='0',
    author="",
    license="",
    description="",
    packages=packages,
    package_dir=packages,
    include_package_data=False,
    install_requires=['pypika']
)
