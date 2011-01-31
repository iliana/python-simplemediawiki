from distutils.core import setup
setup(name='simplemediawiki',
      version='1.0.1',
      description='Extremely low-level wrapper to the MediaWiki API',
      author='Ian Weller',
      author_email='ian@ianweller.org',
      url='http://github.com/ianweller/python-simplemediawiki',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU Library or Lesser General Public '
          'License (LGPL)',
      ],
      requires=[
          'iso8601',
      ],
      py_modules=['simplemediawiki'])
