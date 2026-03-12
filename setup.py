from setuptools import find_packages, setup

setup(
    name='bbp_domain_scraper',
    version='1.1.0',
    packages=find_packages(),
    install_requires=['requests'],
    entry_points={
        'console_scripts': [
            'bbp_domain_scraper=main:main',
        ],
    },
    author='alejandro501',
    description='Bug bounty scope scraper for Bugcrowd and HackerOne',
    url='https://github.com/alejandro501/bbp_domain_scraper',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
