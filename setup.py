# MIT License
#
# Copyright (c) 2016 Patrick Eschenbach
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'name': 'landsat8',
    'description': 'Command line tool for downloading the latest available Landsat8 scene and converting it to a natural color JPG image using the landsat-util library.',
    'author': 'Patrick Eschenbach',
    'author_email': 'paddyesch@gmx.de',
    'version': '0.1',
    'license': 'MIT License',
    'keywords': "landsat satellite scene",
    'url': 'https://github.com/paddyesch/landsat8',
    'download_url': 'https://github.com/paddyesch/landsat8/archive/master.zip',
    'install_requires': ['feedparser', 'colorama', 'landsat-util'],
    'packages': ['landsat8'],
    'scripts': ['bin/landsat8'],
    'classifiers': [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License'
    ]
}

setup(**config)
