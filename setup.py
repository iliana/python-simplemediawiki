from distutils.core import setup
from sphinx.setup_command import BuildDoc

version = '1.0.2'

cmdclass = {'build_sphinx': BuildDoc}
setup(name='simplemediawiki',
      version=version,
      description='Extremely low-level wrapper to the MediaWiki API',
      author='Ian Weller',
      author_email='iweller@redhat.com',
      url='https://github.com/ianweller/python-simplemediawiki',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU Library or Lesser General Public '
          'License (LGPL)',
      ],
      requires=[
          'iso8601',
          'kitchen',
      ],
      py_modules=['simplemediawiki'],
      cmdclass=cmdclass,
      command_options={
          'build_sphinx': {
              'version': ('setup.py', version),
              'release': ('setup.py', version),
          }
      })
