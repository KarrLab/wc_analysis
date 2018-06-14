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
        options (:obj:`dict`): options
    """

    def __init__(self, out_path=None, options=None):
        """
        Args:
            out_path (:obj:`str`, optional): path to save analyses
            options (:obj:`dict`, optional): options
        """
        self.out_path = out_path

        # make the output directory if it doesn't exist
        if out_path and not os.path.isdir(out_path):
            os.makedirs(out_path)

        self.options = options or {}
        self.clean_and_validate_options()

    def clean_and_validate_options(self):
        """ Apply default options and validate options """
        pass

    @abc.abstractmethod
    def run(self):
        """ Run the analysis """
        pass  # pragma: no cover


class KnowledgeBaseAnalysis(Analysis):
    """ Analysis of a knowledge base

    Attributes:
        knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
    """

    def __init__(self, knowledge_base, out_path=None, options=None):
        """
        Args:
            knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
            out_path (:obj:`str`, optional): path to save analyses
            options (:obj:`dict`, optional): options
        """
        super(KnowledgeBaseAnalysis, self).__init__(out_path=out_path, options=options)
        self.knowledge_base = knowledge_base


class ModelAnalysis(Analysis):
    """ Analysis of a model

    Attributes:
        model (:obj:`wc_lang.core.Model`): model
        knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
    """

    def __init__(self, model, knowledge_base, out_path=None, options=None):
        """
        Args:
            model (:obj:`wc_lang.core.Model`): model
            knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
            out_path (:obj:`str`, optional): path to save analyses
            options (:obj:`dict`, optional): options
        """
        super(ModelAnalysis, self).__init__(out_path=out_path, options=options)
        self.model = model
        self.knowledge_base = knowledge_base


class SimulationResultsAnalysis(Analysis):
    """ Analysis of a simulation result

    Attributes:
        sim_results_path (:obj:`str`): path to simulation results
        model (:obj:`wc_lang.core.Model`): model
        knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
    """

    def __init__(self, sim_results_path, model, knowledge_base, out_path=None, options=None):
        """
        Args:
            sim_results_path (:obj:`str`): path to simulation results
            model (:obj:`wc_lang.core.Model`): model
            knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
            out_path (:obj:`str`, optional): path to save analyses
            options (:obj:`dict`, optional): options
        """
        super(SimulationResultsAnalysis, self).__init__(out_path=out_path, options=options)
        self.sim_results_path = sim_results_path
        self.model = model
        self.knowledge_base = knowledge_base


class AnalysisRunner(object):
    """ Run one or more analyses of a whole-cell knowledge base, model, and/or simulation results

    Attributes:
        knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
        model (:obj:`wc_lang.core.Model`): model
        sim_results_path (:obj:`str`): path to simulation results
        analyses (:obj:`list` of :obj:`Analysis`): analyses to run
        out_path (:obj:`str`):  path to save analyses
        options (:obj:`dict`): options
    """

    DEFAULT_ANALYSES = ()

    def __init__(self, knowledge_base, model, sim_results_path, analyses=None, out_path=None, options=None):
        """
        Args:
            knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
            model (:obj:`wc_lang.core.Model`): model
            sim_results_path (:obj:`str`): path to simulation results
            analyses (:obj:`list` of :obj:`Analysis`, optional): analyses to run
            out_path (:obj:`str`, optional): path to save analyses
            options (:obj:`dict`, optional): options
        """
        if analyses is None:
            analyses = self.DEFAULT_ANALYSES

        self.knowledge_base = knowledge_base
        self.model = model
        self.sim_results_path = sim_results_path
        self.analyses = analyses
        self.out_path = out_path
        self.options = options or {}

        self.clean_and_validate_options()

    def clean_and_validate_options(self):
        """ Apply default options and validate options """
        pass

    def run(self):
        """ Run multiple analyses

        Raises:
            :obj:`ValueError`: if the analysis is not supported
        """
        options = self.options.get('analysis', {})
        for analysis_cls in self.analyses:
            if self.out_path:
                out_path = os.path.join(self.out_path, analysis_cls.__name__)
            else:
                out_path = None

            if issubclass(analysis_cls, KnowledgeBaseAnalysis):
                analysis = analysis_cls(knowledge_base=self.knowledge_base,
                                        out_path=out_path,
                                        options=options.get(analysis_cls.__name__, {}))
            elif issubclass(analysis_cls, ModelAnalysis):
                analysis = analysis_cls(knowledge_base=self.knowledge_base,
                                        model=self.model,
                                        out_path=out_path,
                                        options=options.get(analysis_cls.__name__, {}))
            elif issubclass(analysis_cls, SimulationResultsAnalysis):
                analysis = analysis_cls(knowledge_base=self.knowledge_base,
                                        model=self.model,
                                        sim_results_path=self.sim_results_path,
                                        out_path=out_path,
                                        options=options.get(analysis_cls.__name__, {}))
            else:
                raise ValueError('Unsupported analysis of type {}'.format(analysis_cls.__name__))

            analysis.run()
