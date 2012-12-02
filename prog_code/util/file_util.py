"""Logic for interfacing user uploads.

@author: Sam Pottinger
@license: GNU GPL v2
"""


import os
import random
import string

ALLOWED_EXTENSIONS = set(['yaml', 'csv'])
UPLOAD_FOLDER = './uploads'

def upload_exists(filename):
    filename = os.path.join(UPLOAD_FOLDER, filename)
    try:
        with open(filename) as f:
            pass
        return True
    except IOError as e:
        return False

def generate_filename(format, length=8, chars=string.letters):
    return ''.join([random.choice(chars) for i in range(length)]) + format

def generate_unique_filename(format, length=8, chars=string.letters):
    found = False
    possibility = None
    while not found:
        possibility = generate_filename(format, length, chars)
        found = not upload_exists(possibility)
    return possibility

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS