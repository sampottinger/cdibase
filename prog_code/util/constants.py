"""Listing of special values encoded in the database for CDI information.

Copyright (C) 2014 A. Samuel Pottinger ("Sam Pottinger", gleap.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

@author: Sam Pottinger
@license: GNU GPL v3
"""

NO_DATA = -100
UNKNOWN = -200
POSSIBLY_WRONGLY_REC = -300
EMERGENCY_REC = -400
IMPLIED_FALSE = -500
IMPLIED_TRUE = -501
EXPLICIT_TRUE = 4
LEGACY_TRUE = 1
EXPLICIT_FALSE = 0
EXPLICIT_NONE = -600
EXPLICIT_NA = -700
EXPLICIT_OTHER = -800
NO_EXTRA_CATEGORIES = -900
EXTRA_CATEGORIES = -1000
ELEVEN_PRESUMED_TRUE = -3000
TRUE_VALS = [EXPLICIT_TRUE, ELEVEN_PRESUMED_TRUE]

MALE = -2001
FEMALE = -2002
OTHER_GENDER = -2003

ERROR_ATTR = 'error'
CONFIRMATION_ATTR = 'confirmation'
FORMAT_SESSION_ATTR = 'format'
SNAPSHOTS_DB_TABLE = 'snapshots'
FORM_SELECTED_VALUE = 'on'

BASE_URL = '/base'
