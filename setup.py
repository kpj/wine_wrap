from setuptools import setup, find_packages


setup(
    name='wine_wrap',
    version='0.1.0',

    description='A versioned wine-prefix management tool',

    setup_requires=['setuptools-markdown'],
    long_description_markdown_filename='README.md',

    url='https://github.com/kpj/wine_wrap',

    author='kpj',
    author_email='kpjkpjkpjkpjkpjkpj@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: System :: Systems Administration',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only'
    ],

    keywords='wine_wrap wine windows',
    packages=find_packages(exclude=['tests']),

    install_requires=[
        'sh', 'click', 'appdirs'
    ],

    entry_points={
        'console_scripts': [
            'wine_wrap=wine_wrap:main',
        ],
    }
)
