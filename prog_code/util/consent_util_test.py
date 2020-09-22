"""Tests for utility functions used in remote consent forms.

Copyright (C) 2020 A. Samuel Pottinger ("Sam Pottinger", gleap.org)

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
import datetime
import unittest
import unittest.mock

import prog_code.util.consent_util as consent_util
import prog_code.util.constants as constants

from ..struct import models

class ConsentUtilTests(unittest.TestCase):

    def __run_with_mocks(self, body, settings, filings):
        with unittest.mock.patch('prog_code.util.db_util.get_consent_settings') as get_consent_settings:
            with unittest.mock.patch('prog_code.util.db_util.get_consent_filings') as get_consent_filings:
                get_consent_settings.return_value = settings
                get_consent_filings.return_value = filings
                body()

    def __create_settings(self, requirement_type):
        return models.ConsentFormSettings(
            'test-study',
            requirement_type,
            '',
            [],
            datetime.datetime.now()
        )

    def __create_filing(self, child_id, access_key):
        return models.ConsentFormFiling(
            'test-study',
            'test name',
            child_id,
            datetime.datetime.now(),
            [],
            'test@example.com',
            access_key
        )

    def test_requires_consent_form_never(self):
        def body():
            result = consent_util.requires_consent_form(
                'test-1',
                'test-study',
                '1234'
            )
            self.assertFalse(result)

        self.__run_with_mocks(
            body,
            self.__create_settings(constants.CONSENT_FORM_NONE),
            []
        )

    def test_requires_consent_form_always_incomplete(self):
        def body():
            result = consent_util.requires_consent_form(
                'test-1',
                'test-study',
                '1234'
            )
            self.assertTrue(result)

        self.__run_with_mocks(
            body,
            self.__create_settings(constants.CONSENT_FORM_ALWAYS),
            [
                self.__create_filing('test-1', '5678')
            ]
        )

    def test_requires_consent_form_always_complete(self):
        def body():
            result = consent_util.requires_consent_form(
                'test-1',
                'test-study',
                '1234'
            )
            self.assertFalse(result)

        self.__run_with_mocks(
            body,
            self.__create_settings(constants.CONSENT_FORM_ALWAYS),
            [
                self.__create_filing('test-1', '5678'),
                self.__create_filing('test-1', '1234')
            ]
        )

    def test_requires_consent_form_once_no_match_prior(self):
        def body():
            result = consent_util.requires_consent_form(
                'test-1',
                'test-study',
                '5678'
            )
            self.assertTrue(result)

        self.__run_with_mocks(
            body,
            self.__create_settings(constants.CONSENT_FORM_ONCE),
            [
                self.__create_filing('test-2', '1234')
            ]
        )

    def test_requires_consent_form_once_no_prior(self):
        def body():
            result = consent_util.requires_consent_form(
                'test-1',
                'test-study',
                '5678'
            )
            self.assertTrue(result)

        self.__run_with_mocks(
            body,
            self.__create_settings(constants.CONSENT_FORM_ONCE),
            []
        )

    def test_requires_consent_form_once_with_prior(self):
        def body():
            result = consent_util.requires_consent_form(
                'test-1',
                'test-study',
                '5678'
            )
            self.assertFalse(result)

        self.__run_with_mocks(
            body,
            self.__create_settings(constants.CONSENT_FORM_ONCE),
            [
                self.__create_filing('test-1', '1234')
            ]
        )
