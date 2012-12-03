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
    """Check if a file already exists in the uploads directory.

    @param filename: The name of the file to check for.
    @type filename: str
    @return: True if file by the given name already exists and False otherwise.
    @rtype: boolean
    """
    filename = os.path.join(UPLOAD_FOLDER, filename)
    try:
        with open(filename) as f:
            pass
        return True
    except IOError as e:
        return False


def generate_filename(format, length=8, chars=string.letters):
    """Generate a random filename.

    @param format: The file extension to use (ex. ".yaml")
    @type format: str
    @keyword length: The number of non-file extension characters to include in
        the generated filename.
    @type length: int
    @param chars: The set of characters to choose from.
    @type chars: Iterable over characters.
    @return: Random filename
    @rtype: str
    """
    return ''.join([random.choice(chars) for i in range(length)]) + format


def generate_unique_filename(format, length=8, chars=string.letters):
    """Generate a random filename that no other existing file uploads have.

    Generate a filename such that no file in the uploads directory exists with
    the returned filename.

    @param format: The file extension to use (ex. ".yaml")
    @type format: str
    @keyword length: The number of non-file extension characters to include in
        the generated filename.
    @type length: int
    @param chars: The set of characters to choose from.
    @type chars: Iterable over characters.
    @return: Random filename
    @rtype: str
    """
    found = False
    possibility = None
    while not found:
        possibility = generate_filename(format, length, chars)
        found = not upload_exists(possibility)
    return possibility


def allowed_file(filename):
    """Check that the server will accept the file of the given type.

    @param filename: The filename to check for acceptability.
    @type filename: str
    @return: True if acceptable and False otherwise.
    @rtype: bool
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
