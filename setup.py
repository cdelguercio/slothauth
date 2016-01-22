from setuptools import setup
setup(
  name='slothauth',
  packages=['slothauth'],
  install_requires=['factory_boy==2.6.0', 'djangorestframework==3.3.2',],
  version='0.2',
  description='A Python Django package for user accounts and authentication.',
  author='Chris Del Guercio',
  author_email='cdelguercio@gmail.com',
  url='https://github.com/cdelguercio/slothauth',
  download_url='https://github.com/cdelguercio/slothauth/tarball/0.2',
  keywords=['slothauth', 'sloth', 'auth', 'accounts', 'users', 'django', 'python'],
  classifiers=[],
  test_suite='nose.collector',
  tests_require=['nose', 'nose-cover3'],
  include_package_data=True,
)
