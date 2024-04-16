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
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    zip_safe=False,
    project_urls={
        'Bug Reports': 'https://github.com/martyanov/aonvif/issues',
        'Repository': 'https://github.com/martyanov/aonvif',
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
        'aonvif.wsdl': [
            '**/*',
        ],
    },
    python_requires='>=3.9.1,<4',
    setup_requires=[
        'setuptools_scm==6.3.2',
    ],
    install_requires=[
        'zeep[async]>=4,<5',
    ],
    extras_require={
        'dev': [
            'flake8-bugbear==22.10.27',
            'flake8-commas==2.1.0',
            'flake8-comprehensions==3.10.1',
            'flake8-isort==5.0.3',
            'flake8==6.0.0',
            'pep8-naming==0.13.2',
            'twine==4.0.2',
        ],
        'test': [
            'pytest-asyncio==0.20.2',
            'pytest-cov==4.0.0',
            'pytest==7.2.0',
            'pytest-mock==3.14.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'aonvif-cli=aonvif.cli:main',
        ],
    },
)
