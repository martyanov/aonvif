import setuptools


def _get_long_description():
    with open('README.rst') as readme_file:
        return readme_file.read()


setuptools.setup(
    name='aonvif',
    use_scm_version=True,
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
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    zip_safe=False,
    project_urls={
        'Bug Reports': 'https://github.com/martyanov/onvif/issues',
        'Repository': 'https://github.com/martyanov/onvif',
    },
    packages=setuptools.find_packages(
        exclude=[
            'examples',
            'tests',
        ],
    ),
    package_data={
        '': [
            '*.rst',
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
    python_requires='>=3.7,<4',
    setup_requires=[
        'setuptools_scm==6.3.2',
    ],
    install_requires=[
        'zeep[async]>=4,<5',
    ],
    extras_require={
        'dev': [
            'flake8-broken-line==0.4.0',
            'flake8-bugbear==21.11.29',
            'flake8-commas==2.1.0',
            'flake8-comprehensions==3.7.0',
            'flake8-isort==4.1.1',
            'flake8-quotes==3.3.1',
            'flake8==4.0.1',
            'pep8-naming==0.12.1',
            'twine==3.7.1',
        ],
        'test': [
            'pytest-asyncio==0.16.0',
            'pytest-cov==3.0.0',
            'pytest==6.2.5',
        ],
    },
    entry_points={
        'console_scripts': [
            'onvif-cli=onvif.cli:main',
        ],
    },
)
