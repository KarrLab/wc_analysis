import pkg_resources

with open(pkg_resources.resource_filename('wc_analysis', 'VERSION'), 'r') as file:
    __version__ = file.read().strip()
# :obj:`str`: version

# API
from .core import Analysis, KnowledgeBaseAnalysis, ModelAnalysis, SimulationResultsAnalysis, AnalysisRunner
