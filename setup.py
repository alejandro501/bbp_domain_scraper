from setuptools import setup, find_packages

setup(
    name='bbp_domain_scraper',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'PyYAML',
        'requests',
        'beautifulsoup4',
    ],
    entry_points={
        'console_scripts': [
            'bbp_domain_scraper=main:main', 
        ],
    },
    author='alejandro501',
    description='Life\'s too short for a short description',
    url='https://github.com/alejandro501/bbp_domain_scraper',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
