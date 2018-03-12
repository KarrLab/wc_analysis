""" Tests API

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-03-12
:Copyright: 2018, Karr Lab
:License: MIT
"""

import wc_analysis
import types
import unittest


class ApiTestCase(unittest.TestCase):
    def test(self):
        self.assertIsInstance(wc_analysis, types.ModuleType)
        self.assertIsInstance(wc_analysis.Analysis, type)
