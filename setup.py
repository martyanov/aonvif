import setuptools


def _get_long_description():
    with open('README.rst') as readme_file:
        return readme_file.read()


setuptools.setup(
    name='aonvif',
    version='0.1.0rc2',
    description='ONVIF asynchronous client implementation in Python',
    long_description=_get_long_description(),
    author='Andrey Martyanov',
    author_email='andrey@martyanov.com',
    url='https://github.com/martyanov/aonvif',
    license='MIT',
    keywords=['onvif', 'client', 'asyncio'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    zip_safe=False,
    project_urls={
        'Bug Reports': 'https://github.com/martyanov/onvif/issues',
        'Repository': 'https://github.com/martyanov/onvif',
    },
    python_requires='>=3.7,<4.0',
    packages=setuptools.find_packages(
        exclude=[
            'docs',
            'examples',
            'tests',
        ],
    ),
    package_data={
        '': [
            '*.txt',
            '*.rst',
        ],
        'onvif': [
            '*.wsdl',
            '*.xsd',
            '*xml*',
            'envelope',
            'include',
            'addressing',
        ],
        'onvif.wsdl': [
            '*.wsdl',
            '*.xsd',
            '*xml*',
            'envelope',
            'include',
            'addressing',
        ],
    },
    install_requires=[
        'aiohttp>=1.0,<4.0',
        'zeep[async]>=3.0,<=4.0',
    ],
    entry_points={
        'console_scripts': [
            'onvif-cli = onvif.cli:main',
        ],
    },
)
