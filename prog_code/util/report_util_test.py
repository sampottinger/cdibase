import mox

import report_util


class TestMCDIFormat:

    def __init__(self, details):
        self.details = details


class ReportUtilTest(mox.MoxTestBase):

    def test_sort_by_study_order(self):
        test_rows = [[0]]* 20 + [['word1'], ['word3'], ['word2'], ['word4']]
        test_format = TestMCDIFormat(
            {'categories': [
                {'words': ['word1', 'word2']},
                {'words': ['word3', 'word4']}
            ]}
        )
        sorted_rows = report_util.sort_by_study_order(test_rows, test_format)
        self.assertEqual(sorted_rows[20][0], 'word1')
        self.assertEqual(sorted_rows[21][0], 'word2')
        self.assertEqual(sorted_rows[22][0], 'word3')
        self.assertEqual(sorted_rows[23][0], 'word4')
