
import sys
import os

extensions = [
    'sphinx.ext.todo',
]

source_suffix = '.txt'

master_doc = 'index'

### part to update ###################################
project = u'domogik-plugin-ebusd'
copyright = u'2016, Tikismoke'
version = '0.1'
release = version
######################################################

pygments_style = 'sphinx'

html_theme = 'default'
html_static_path = ['_static']
