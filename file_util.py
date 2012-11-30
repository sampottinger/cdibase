import os
import random
import string

ALLOWED_EXTENSIONS = set(['yaml'])
UPLOAD_FOLDER = './uploads'

def upload_exists(filename):
    filename = os.path.join(UPLOAD_FOLDER, filename)
    try:
        with open(filename) as f:
            pass
        return True
    except IOError as e:
        return False

def generate_filename(length=8, chars=string.letters):
    return ''.join([random.choice(chars) for i in range(length)]) + ".yaml"

def generate_unique_filename(length=8, chars=string.letters):
    found = False
    possibility = None
    while not found:
        possibility = generate_filename(length, chars)
        found = not upload_exists(possibility)
    return possibility