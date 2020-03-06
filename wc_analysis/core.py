""" Analyze knowledge base, model, and simulation results.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2018-02-13
:Copyright: 2018, Karr Lab
:License: MIT
"""

from matplotlib import pyplot
import abc
import matplotlib
import os
import wc_kb.core
import wc_lang.core


class Analysis(object, metaclass=abc.ABCMeta):
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

    def create_fig(self, rows=1, cols=1):
        """ Create a figure composed of a grid of subfigures

        Args:
            rows (:obj:`int`, optional): number of rows of subfigures
            cols (:obj:`int`, optional): number of columns of subfigures

        Returns:
            :obj:`matplotlib.figure.Figure`: figure
            :obj:`matplotlib.axes.Axes`: axes
        """
        return pyplot.subplots(nrows=rows, ncols=cols)

    def show_or_save_fig(self, fig, filename=None):
        """ Show or save a figure

        Args:
            fig (:obj:`matplotlib.figure.Figure`): figure
            filename (:obj:`str`, optional): filename to save figure
        """
        if self.out_path:
            fig.savefig(os.path.join(self.out_path, filename), transparent=True, bbox_inches='tight')
            pyplot.close(fig)
        else:
            fig.show()  # pragma: no cover


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

    def __init__(self, model, knowledge_base=None, out_path=None, options=None):
        """
        Args:
            model (:obj:`wc_lang.core.Model`): model
            knowledge_base (:obj:`wc_kb.core.KnowledgeBase`, optional): knowledge base
            out_path (:obj:`str`, optional): path to save analyses
            options (:obj:`dict`, optional): options
        """
        super(ModelAnalysis, self).__init__(out_path=out_path, options=options)
        self.model = model
        self.knowledge_base = knowledge_base


class SimulationAnalysis(Analysis):
    """ Analysis of a simulation result

    Attributes:
        sim_results_path (:obj:`str`): path to simulation results
        model (:obj:`wc_lang.core.Model`): model
        knowledge_base (:obj:`wc_kb.core.KnowledgeBase`): knowledge base
    """

    def __init__(self, sim_results_path, model=None, knowledge_base=None, out_path=None, options=None):
        """
        Args:
            sim_results_path (:obj:`str`): path to simulation results
            model (:obj:`wc_lang.core.Model`, optional): model
            knowledge_base (:obj:`wc_kb.core.KnowledgeBase`, optional): knowledge base
            out_path (:obj:`str`, optional): path to save analyses
            options (:obj:`dict`, optional): options
        """
        super(SimulationAnalysis, self).__init__(out_path=out_path, options=options)
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

    def __init__(self, knowledge_base=None, model=None, sim_results_path=None,
        analyses=None, out_path=None, options=None):
        """
        Args:
            knowledge_base (:obj:`wc_kb.core.KnowledgeBase`, optional): knowledge base
            model (:obj:`wc_lang.core.Model`, optional): model
            sim_results_path (:obj:`str`, optional): path to simulation results
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
            elif issubclass(analysis_cls, SimulationAnalysis):
                analysis = analysis_cls(knowledge_base=self.knowledge_base,
                                        model=self.model,
                                        sim_results_path=self.sim_results_path,
                                        out_path=out_path,
                                        options=options.get(analysis_cls.__name__, {}))
            else:
                raise ValueError('Unsupported analysis of type {}'.format(analysis_cls.__name__))

            analysis.run()
