from distutils.core import setup

setup(
  name         = 'nagios-check_multiple',
  version      = '0.0.1',
  maintainer       = 'Clark A',
  maintainer_email = 'clarka@gmail.com',
  url          = 'https://github.com/clarkbox/check_multiple',
  scripts      = ['check_multiple.py'],
  description  = 'Run multiple Nagios checks and combine the results',
  long_description=open('README.md').read(),
  classifiers  = [
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Environment :: Console',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: MIT License',
  ]
)
