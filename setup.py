import sys
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version='1.2.0b2'
cmdclass = {}
command_options = {}
install_requires = []

# If sphinx is installed, enable the command
try:
    from sphinx.setup_command import BuildDoc
    cmdclass['build_sphinx'] = BuildDoc
    command_options['build_sphinx'] = {
        'version': ('setup.py', version),
        'release': ('setup.py', version),
    }
except ImportError:
    pass

if sys.version_info[0] == 2:
    install_requires.append('kitchen')

setup(name='simplemediawiki',
      version=version,
      description='Extremely low-level wrapper to the MediaWiki API',
      author='Ian Weller',
      author_email='iweller@redhat.com',
      url='https://github.com/ianweller/python-simplemediawiki',
      classifiers=[
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU Library or Lesser General Public '
          'License (LGPL)',
      ],
      install_requires=install_requires,
      py_modules=['simplemediawiki'],
      cmdclass=cmdclass,
      command_options=command_options)
