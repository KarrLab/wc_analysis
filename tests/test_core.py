""" Tests of analyses

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-02-11
:Copyright: 2018, Karr Lab
:License: MIT
"""

from wc_analysis import core
import os
import shutil
import tempfile
import unittest


class Test(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_Analysis(self):
        with self.assertRaisesRegexp(TypeError, 'Can\'t instantiate abstract class'):
            core.Analysis()

        class TestAnalysis(core.Analysis):
            def run(self):
                pass

        out_path = os.path.join(self.dir, 'test_analysis')
        test_analysis = TestAnalysis(out_path=out_path)
        test_analysis.run()
        self.assertTrue(os.path.isdir(out_path))

    def test_KnowledgeBaseAnalysis(self):
        class TestAnalysis(core.KnowledgeBaseAnalysis):
            def run(self):
                pass

        test_analysis = TestAnalysis(knowledge_base=None)
        test_analysis.run()

    def test_ModelAnalysis(self):
        class TestAnalysis(core.ModelAnalysis):
            def run(self):
                pass

        test_analysis = TestAnalysis(model=None, knowledge_base=None)
        test_analysis.run()

    def test_SimulationAnalysis(self):
        class TestAnalysis(core.SimulationAnalysis):
            def run(self):
                pass

        test_analysis = TestAnalysis(sim_results_path=self.dir, model=None, knowledge_base=None)
        test_analysis.run()

    def test_AnalysisRunner_constructor(self):
        runner = core.AnalysisRunner(None, None, None)
        self.assertEqual(runner.analyses, ())

    def test_AnalysisRunner_without_saving(self):
        class TestKbAnalysis(core.KnowledgeBaseAnalysis):
            def run(self):
                pass

        class TestModelAnalysis(core.ModelAnalysis):
            def run(self):
                pass

        class TestSimResultsAnalysis(core.SimulationAnalysis):
            def run(self):
                pass
        runner = core.AnalysisRunner(None, None, None, analyses=[
            TestKbAnalysis, TestModelAnalysis, TestSimResultsAnalysis,
        ])
        runner.run()
        self.assertFalse(os.path.isdir(os.path.join(self.dir, 'TestKbAnalysis')))
        self.assertFalse(os.path.isdir(os.path.join(self.dir, 'TestModelAnalysis')))
        self.assertFalse(os.path.isdir(os.path.join(self.dir, 'TestSimResultsAnalysis')))

    def test_AnalysisRunner_with_saving(self):
        class TestKbAnalysis(core.KnowledgeBaseAnalysis):
            def run(self):
                pass

        class TestModelAnalysis(core.ModelAnalysis):
            def run(self):
                pass

        class TestSimResultsAnalysis(core.SimulationAnalysis):
            def run(self):
                pass
        runner = core.AnalysisRunner(None, None, None, analyses=[
            TestKbAnalysis, TestModelAnalysis, TestSimResultsAnalysis,
        ], out_path=self.dir)
        runner.run()
        self.assertTrue(os.path.isdir(os.path.join(self.dir, 'TestKbAnalysis')))
        self.assertTrue(os.path.isdir(os.path.join(self.dir, 'TestModelAnalysis')))
        self.assertTrue(os.path.isdir(os.path.join(self.dir, 'TestSimResultsAnalysis')))

    def test_AnalysisRunner_error(self):
        class TestAnalysis(core.Analysis):
            def run(self):
                pass
        runner = core.AnalysisRunner(None, None, None, analyses=[TestAnalysis], out_path=self.dir)
        with self.assertRaisesRegexp(ValueError, 'Unsupported analysis of '):
            runner.run()
