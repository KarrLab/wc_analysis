""" Analyze FBA model

:Author: Arthur Goldberg <athur.p.goldberg@mssm.edu>
:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2018-11-26
:Copyright: 2018, Karr Lab
:License: MIT
"""

from wc_analysis.core import ModelAnalysis
from wc_onto import onto
import networkx
import wc_kb
import wc_lang
import wc_lang.config


class FbaModelAnalysis(ModelAnalysis):
    """ Statically analyze an FBA submodel

    * Find reaction gaps
    * Find dead end species

    Attributes:
        submodel (:obj:`wc_lang.Submodel`): dFBA submodel
    """

    def run(self, model, knowledge_base=None, out_path=None, options=None):
        """
        Args:
            model (:obj:`wc_lang.Model`): model
            knowledge_base (:obj:`wc_kb.KnowledgeBase`, optional): knowledge base
            out_path (:obj:`str`, optional): path to save analyses
            options (:obj:`dict`, optional): options
        """
        super(FbaModelAnalysis, self).__init__(model, knowledge_base=knowledge_base,
                                               out_path=out_path, options=options)

        for submodel in self.model.submodels:
            if submodel.framework != onto['WC:dynamic_flux_balance_analysis']:
                self.get_rxn_gaps(submodel)
                self.path_bounds_analysis(submodel)

    def get_rxn_gaps(self, submodel):
        """ Identify gaps in a dFBA submodel's reaction network

        Species that are not consumed or not produced indicate gaps in the reaction network.
        These can be found by a static analysis of the model. Reactions that use species that
        are not produced or produce species that are not consumed must eventually have zero flux.
        A reaction network can be reduced to a minimal network of reactions that can all
        have positive fluxes.

        Algorithm::

            all_gap_species = get_gap_species([])
            delta_gap_species = all_gap_species
            while delta_gap_species:
                all_gap_reactions = get_gap_reactions(all_gap_species)
                tmp_gap_species = all_gap_species
                all_gap_species = get_gap_species(all_gap_reactions)
                delta_gap_species = all_gap_species - tmp_gap_species
            return (all_gap_species, all_gap_reactions)

        Args:
            submodel (:obj:`wc_lang.Submodel`): dFBA submodel

        Returns:
            * :obj:`set` of :obj:`wc_lang.Species`: `Species` not in the minimal reaction network
            * :obj:`set` of :obj:`wc_lang.Reaction`: `Reaction`s not in the minimal reaction network
        """
        all_dead_end_species = self.get_dead_end_species(submodel, set())
        delta_dead_end_species = all_dead_end_species
        inactive_reactions = set()
        while any(delta_dead_end_species):
            inactive_reactions = self.get_inactive_rxns(submodel, all_dead_end_species)
            tmp_not_consumed, tmp_not_produced = all_dead_end_species
            all_dead_end_species = self.get_dead_end_species(submodel, inactive_reactions)
            all_not_consumed, all_not_produced = all_dead_end_species
            delta_dead_end_species = (all_not_consumed-tmp_not_consumed, all_not_produced-tmp_not_produced)
        return (all_dead_end_species, inactive_reactions)

    def get_dead_end_species(self, submodel, inactive_reactions):
        """ Find the dead end species in a reaction network

        Given a set of inactive reactions in submodel, determine species that are not consumed by
        any reaction, or are not produced by any reaction. Costs :math:`O(n*p)`, where :math:`n` is
        the number of reactions in `submodel` and :math:`p` is the maximum number of participants in
        a reaction.

        Args:
            submodel (:obj:`wc_lang.Submodel`): dFBA submodel
            inactive_reactions (:obj:`set` of :obj:`wc_lang.Reaction`): the inactive reactions in `submodel`

        Returns:
            :obj:`tuple`:

                * :obj:`set` of :obj:`wc_lang.Species`: the species that are not consumed
                * :obj:`set` of :obj:`wc_lang.Species`: the species that are not produced
        """
        species = submodel.get_children(kind='submodel', __type=wc_lang.Species)
        species_not_consumed = set(species)
        species_not_produced = set(species)
        for rxn in submodel.reactions:
            if rxn in inactive_reactions:
                continue
            if rxn.reversible:
                for part in rxn.participants:
                    species_not_consumed.discard(part.species)
                    species_not_produced.discard(part.species)
            else:
                for part in rxn.participants:
                    if part.coefficient < 0:
                        species_not_consumed.discard(part.species)
                    elif 0 < part.coefficient:
                        species_not_produced.discard(part.species)
        return (species_not_consumed, species_not_produced)

    def get_inactive_rxns(self, submodel, dead_end_species):
        """ Find the inactive reactions in a reaction network

        Given the dead end species in a reaction network, find the reactions that must eventually
        become inactive. Reactions that consume species which are not produced must become inactive.
        And reactions that produce species which are not consumed must become inactive to prevent
        the copy numbers of those species from growing without bound.
        Costs :math:`O(n*p)`, where :math:`n` is the number of reactions in `submodel` and :math:`p`
        is the maximum number of participants in a reaction.

        Args:
            submodel (:obj:`wc_lang.Submodel`): dFBA submodel
            dead_end_species (:obj:`tuple`):

                * :obj:`set` of :obj:`wc_lang.Species`: the `Species` that are not consumed by any `Reaction` in `submodel`
                * :obj:`set` of :obj:`wc_lang.Species`: the `Species` that are not produced by any `Reaction` in `submodel`

        Returns:
            :obj:`set` of :obj:`wc_lang.Reaction`: the inactive reactions in `submodel`'s reaction network
        """
        species_not_consumed, species_not_produced = dead_end_species
        inactive_reactions = []
        for rxn in submodel.reactions:
            for part in rxn.participants:
                if (part.species in species_not_consumed or
                        part.species in species_not_produced):
                    inactive_reactions.append(rxn)
                    break
        return inactive_reactions

    def get_digraph(self, submodel):
        """ Create a NetworkX network representing the reaction network in `submodel`

        To leverage the algorithms in NetworkX, map a reaction network on to a NetworkX
        directed graph.
        The digraph is bipartite, with `Reaction` and `Species` nodes. A reaction is represented
        a Reaction node, with an edge from each reactant Species node to the Reaction node, and
        an edge from the Reaction node to each product Species node.

        Args:
            submodel (:obj:`wc_lang.Submodel`): dFBA submodel

        Returns:
            :obj:`networkx.DiGraph`: a NetworkX directed graph representing `submodel`'s reaction network
        """
        digraph = networkx.DiGraph()

        # make network of obj_model.Model instances
        for specie in submodel.get_children(kind='submodel', __type=wc_lang.Species):
            digraph.add_node(specie)
        for rxn in submodel.reactions:
            digraph.add_node(rxn)
            for participant in rxn.participants:
                part = participant.species
                if participant.coefficient < 0:
                    # reactant
                    digraph.add_edge(part, rxn)
                elif 0 < participant.coefficient:
                    # product
                    digraph.add_edge(rxn, part)
            if rxn.reversible:
                for participant in rxn.participants:
                    part = participant.species
                    if participant.coefficient < 0:
                        # product
                        digraph.add_edge(rxn, part)
                    elif 0 < participant.coefficient:
                        # reactant
                        digraph.add_edge(part, rxn)
        return digraph

    def path_bounds_analysis(self, submodel):
        """ Perform path bounds analysis on `submodel`

        To be adequately constrained, a dFBA metabolic model should have the property that each path
        from an extracellular species to a component in the objective function contains at least
        one reaction constrained by a finite flux upper bound.

        Analyze the reaction network in `submodel` and return all paths from extracellular species
        to objective function components that lack a finite flux upper bound.

        Args:
            submodel (:obj:`wc_lang.Submodel`): dFBA submodel

        Returns:
            :obj:`dict` of :obj:`list` of :obj:`list` of :obj:`object`: paths from extracellular species to objective
            function components that lack a finite flux upper bound. Keys in the `dict` are the ids
            of extracellular species; the corresponding values contain the unbounded paths for the
            extracellular species, as returned by `unbounded_paths`.
        """
        # todo: symmetrically, report reactions not on any path from ex species to obj fun components
        config = wc_lang.config.get_config()['wc_lang']
        digraph = self.get_digraph(submodel)
        obj_fn_species = submodel.dfba_obj.get_products()
        ex_compartment = submodel.model.compartments.get_one(id=config['EXTRACELLULAR_COMPARTMENT_ID'])
        ex_species = filter(lambda species: species.compartment == ex_compartment,
                            submodel.get_children(kind='submodel', __type=wc_lang.Species))
        all_unbounded_paths = dict()
        for ex_specie in ex_species:
            paths = self.unbounded_paths(digraph, ex_specie, obj_fn_species)
            all_unbounded_paths[ex_specie.id] = paths
        return all_unbounded_paths

    def unbounded_paths(self, rxn_network, ex_species, obj_fn_species, min_non_finite_ub=1000.0):
        """ Find the unbounded paths from an extracellular species to some objective function species

        Return all paths in a reaction network that lack a finite flux upper bound
        and go from `ex_species` to an objective function component.

        Args:
            rxn_network (:obj:`networkx.DiGraph`): a NetworkX directed graph representing a reaction network,
                created by `get_digraph`
            ex_species (:obj:`wc_lang.Species`): an extracellular `Species` that is a node in `rxn_network`
            obj_fn_species (:obj:`list` of :obj:`wc_lang.Species`): objective function `Species` that are
                also nodes in `rxn_network`
            finite_upper_bound_limit (:obj:`float`, optional): the maximum value of a finite flux
                upper bound
            min_non_finite_ub (:obj:`float`, optional): flux upper bounds less than `min_non_finite_ub`
                are considered finite

        Returns:
            :obj:`list` of :obj:`list` of :obj:`object`: a list of the reaction paths from `ex_species`
            to objective function components that lack a finite flux upper bound.
            A path is a list of `Species`, `Reaction`, `Species`, ..., `Species`, starting with
            `ex_species` and ending with an objective function component.

        Raises:
            :obj:`ValueError`: if `ex_species` is not an instance of :obj:`wc_lang.Species` or `obj_fn_species`
                is not a list of instances of :obj:`wc_lang.Species`
        """
        # todo: replace the constant in min_non_finite_ub=1000.0
        unbounded_paths = list()
        if not isinstance(ex_species, wc_lang.Species):
            raise ValueError("'ex_species' should be a wc_lang.Species instance, but it is a {}".format(
                type(ex_species).__name__))
        for of_specie in obj_fn_species:
            if not isinstance(of_specie, wc_lang.Species):
                raise ValueError("elements of 'obj_fn_species' should be wc_lang.Species instances, but one is a {}".format(
                    type(of_specie).__name__))
            for path in networkx.all_simple_paths(rxn_network, source=ex_species, target=of_specie):
                # path is a list of Species, Reaction, ..., Species
                bounded = False
                for i in range(1, len(path), 2):
                    rxn = path[i]
                    if rxn.flux_bounds and rxn.flux_bounds.max < min_non_finite_ub:
                        bounded = True
                        break
                if not bounded:
                    unbounded_paths.append(path)
        return unbounded_paths
