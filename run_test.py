"""
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
"""


import unittest

import daxlabbase

#from prog_code.controller.access_data_controllers_test import *
#from prog_code.controller.account_controllers_test import *
#from prog_code.controller.api_key_controllers_test import *
#from prog_code.controller.delete_data_controllers_test import *
#from prog_code.controller.edit_parent_controllers_test import *
#from prog_code.controller.edit_user_controllers_test import *
#from prog_code.controller.enter_data_controllers_test import *

from prog_code.util.api_key_util_test import *
from prog_code.util.legacy_csv_import_util_test import *
from prog_code.util.new_csv_import_util_test import *
from prog_code.util.db_util_test import *
from prog_code.util.file_util_test import *
from prog_code.util.filter_util_test import *
from prog_code.util.interp_util_test import *
from prog_code.util.mail_util_test import *
from prog_code.util.math_util_test import *
from prog_code.util.oper_interp_test import *
from prog_code.util.parent_account_util_test import *
from prog_code.util.recalc_util_test import *
#from prog_code.util.report_util_test import *


if __name__ == '__main__':
    daxlabbase.disable_email()
    unittest.main()
