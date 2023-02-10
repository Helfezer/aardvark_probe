from setuptools import setup, find_packages
from setuptools.command.install import install

# Setting up
setup(
        name="aardvark_probe", 
        version='0.0.2',
        author="Quentin Pantostier",
        description='Wrapper for Panduza MQTT Calls',
        readme = "README.md",
        packages=find_packages(where='src'),
        package_dir = {"": "src"},
        install_requires=['aardvark_py'],
)

