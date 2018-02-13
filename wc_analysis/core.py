""" Analyze knowledge base, model, and simulation results.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2018-02-13
:Copyright: 2018, Karr Lab
:License: MIT
"""

import abc
import os
import six
import wc_kb.core
import wc_lang.core


class Analysis(six.with_metaclass(abc.ABCMeta, object)):
    """ An analysis of a knowledge base, model, or simulation results

    Attributes:
        out_path (:obj:`str`): optional path to save analysis
    """

    def __init__(self, out_path=None):
        """
        Args:
            out_path (:obj:`str`, optional): path to save analyses
        """
        self.out_path = out_path

        # make the output directory if it doesn't exist
        if out_path and not os.path.isdir(out_path):
            os.makedirs(out_path)

    @abc.abstractmethod
    def run(self):
        """ Run the analysis """
        pass  # pragma: no cover


class KnowledgeBaseAnalysis(Analysis):
    """ Analysis of a knowledge base

    Attributes:
        knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
    """

    def __init__(self, knowledge_base, out_path=None):
        """
        Args:
            knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
            out_path (:obj:`str`, optional): path to save analyses
        """
        super(KnowledgeBaseAnalysis, self).__init__(out_path=out_path)
        self.knowledge_base = knowledge_base


class ModelAnalysis(Analysis):
    """ Analysis of a model

    Attributes:
        model (:obj:`wc_lang.core.Model`): model
        knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
    """

    def __init__(self, model, knowledge_base, out_path=None):
        """
        Args:
            model (:obj:`wc_lang.core.Model`): model
            knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
            out_path (:obj:`str`, optional): path to save analyses
        """
        super(ModelAnalysis, self).__init__(out_path=out_path)
        self.model = model
        self.knowledge_base = knowledge_base


class SimulationResultsAnalysis(Analysis):
    """ Analysis of a simulation result

    Attributes:
        sim_results_path (:obj:`str`): path to simulation results
        model (:obj:`wc_lang.core.Model`): model
        knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
    """

    def __init__(self, sim_results_path, model, knowledge_base, out_path=None):
        """
        Args:
            sim_results_path (:obj:`str`): path to simulation results
            model (:obj:`wc_lang.core.Model`): model
            knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
            out_path (:obj:`str`, optional): path to save analyses
        """
        super(SimulationResultsAnalysis, self).__init__(out_path=out_path)
        self.sim_results_path = sim_results_path
        self.model = model
        self.knowledge_base = knowledge_base


class AnalysisRunner(object):
    """ Run multiple analyses

    Attributes:
        knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
        model (:obj:`wc_lang.core.Model`): model
        sim_results_path (:obj:`str`): path to simulation results
        analyses (:obj:`list` of :obj:`Analysis`): analyses
        out_path (:obj:`str`): optional path to save analysis
    """

    DEFAULT_ANALYSES = ()

    def __init__(self, knowledge_base=None, model=None, sim_results_path=None, analyses=None, out_path=None):
        """
        Args:
            knowledge_base (:obj:`wc_kb.core.KnowledgeBase`, optional): knowledge base
            model (:obj:`wc_lang.core.Model`, optional): model
            sim_results_path (:obj:`str`, optional): path to simulation results
            analyses (:obj:`list` of :obj:`Analysis`, optional): analyses
            out_path (:obj:`str`, optional): optional path to save analysis
        """
        if analyses is None:
            analyses = self.DEFAULT_ANALYSES

        self.knowledge_base = knowledge_base
        self.model = model
        self.sim_results_path = sim_results_path
        self.analyses = analyses
        self.out_path = out_path

    def run(self):
        """ Run multiple analyses

        Raises:
            :obj:`ValueError`: if the analysis is not supported
        """
        for analysis_cls in self.analyses:
            if self.out_path:
                out_path = os.path.join(self.out_path, analysis_cls.__name__)
            else:
                out_path = None

            if issubclass(analysis_cls, KnowledgeBaseAnalysis):
                analysis = analysis_cls(out_path=out_path,
                                        knowledge_base=self.knowledge_base)
            elif issubclass(analysis_cls, ModelAnalysis):
                analysis = analysis_cls(out_path=out_path,
                                        knowledge_base=self.knowledge_base,
                                        model=self.model)
            elif issubclass(analysis_cls, SimulationResultsAnalysis):
                analysis = analysis_cls(out_path=out_path,
                                        knowledge_base=self.knowledge_base,
                                        model=self.model,
                                        sim_results_path=self.sim_results_path)
            else:
                raise ValueError('Unsupported analysis of type {}'.format(analysis_cls.__name__))

            analysis.run()
