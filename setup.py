from setuptools import setup, find_packages
from setuptools.command.install import install

class CustomInstallCommand(install):
    def run(self):
        install.run(self)

# Setting up
setup(
        name="aardvark_probe", 
        version='0.0.1',
        author="Quentin Pantostier",
        description='Wrapper for Panduza MQTT Calls',
        readme = "README.md",
        packages=find_packages(where='src'),
        cmdclass={'install': CustomInstallCommand},

        python_requires = ">=3.6",

        install_requires=['aardvark_py'],
)