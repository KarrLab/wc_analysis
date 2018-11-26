""" Tests analysis of a FBA model

:Author: Arthur Goldberg <athur.p.goldberg@mssm.edu>
:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2018-11-26
:Copyright: 2018, Karr Lab
:License: MIT
"""
import os
import unittest
import wc_lang
import wc_lang.io
import wc_analysis.model.fba

class FbaModelAnalysisTestCase(unittest.TestCase):
    MODEL_FILENAME = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'test_model.xlsx')
    RNX_ID_PREFIX = 'rxn'
    SPECIES_ID_PREFIX = 'spec_type'
    default_max_flux = 10000

    def rxn_id(self, n):
        return "{}_{}".format(self.RNX_ID_PREFIX, n)

    def sp_id(self, n):
        return "{}_{}".format(self.SPECIES_ID_PREFIX, n)

    def next_id(self):
        self.id_idx += 1
        return self.rxn_id(self.id_idx)

    def setUp(self):
        # make model
        self.model = wc_lang.Model(id='model')
        comp = self.model.compartments.create(id='comp')
        self.species = []
        self.num_species = 20
        for i in range(1, self.num_species+1):
            spec_type = self.model.species_types.create(id=self.sp_id(i),
                                                        type=wc_lang.SpeciesTypeType.metabolite)
            self.species.append(wc_lang.Species(
                id=wc_lang.Species.gen_id(spec_type.id, comp.id),
                species_type=spec_type,
                compartment=comp))
        self.dfba_submodel = self.model.submodels.create(
            id='metabolism', algorithm=wc_lang.SubmodelAlgorithm.dfba)

        self.id_idx = 0
        self.model_analysis = wc_analysis.model.fba.FbaModelAnalysis(self.model)

    def make_reaction(self, submodel, reactant, product, **kwargs):
        reversible = True
        if 'reversible' in kwargs:
            reversible = kwargs['reversible']
        max_flux = self.default_max_flux
        if 'max_flux' in kwargs:
            max_flux = kwargs['max_flux']
        rxn = submodel.reactions.create(id=self.next_id(), reversible=reversible, max_flux=max_flux)
        rxn.participants.create(species=reactant, coefficient=-1)
        rxn.participants.create(species=product, coefficient=1)

    def create_reaction_network(self, submodel, network_type, **kwargs):
        # make networks of reactions with 1 reactant and 1 product
        # first delete all Reactions
        submodel.reactions = []
        if network_type == 'ring':
            # kwargs options: num_rxn, reversible, max_flux
            species = self.species
            if len(species) < kwargs['num_rxn']:
                self.fail("not enough species, len(species) < kwargs['num_rxn']")
            for reactant_idx in range(kwargs['num_rxn']):
                product_idx = (reactant_idx+1) % kwargs['num_rxn']
                self.make_reaction(submodel, species[reactant_idx], species[product_idx], **kwargs)
        else:
            self.Fail("Unknown network type: {}".format(network_type))

    def test_get_inactive_reactions(self):
        # make ring of 3 irreversible reactions
        self.create_reaction_network(self.dfba_submodel, 'ring', **{'num_rxn': 3, 'reversible': False})

        # no dead end species -> no inactive reactions
        self.assertEqual(self.model_analysis.get_inactive_rxns(self.dfba_submodel, (set(), set())), [])

        # one dead end species -> 2 inactive reactions
        first_specie = self.species[0]
        dead_end_species = set([first_specie])
        inactive_reactions = self.model_analysis.get_inactive_rxns(self.dfba_submodel,
                                                                       (set(), dead_end_species))
        self.assertEqual(len(inactive_reactions), 2)
        self.assertIn(self.dfba_submodel.reactions[0], inactive_reactions)
        self.assertIn(self.dfba_submodel.reactions[-1], inactive_reactions)

    def test_find_dead_end_species(self):
        model_analysis = self.model_analysis

        # make ring of 4 irreversible reactions
        self.create_reaction_network(self.dfba_submodel, 'ring', **{'num_rxn': 4, 'reversible': False})

        # ring with no inactive reactions -> no dead end species
        species_not_consumed, species_not_produced = model_analysis.get_dead_end_species(self.dfba_submodel, set())
        self.assertFalse(species_not_consumed)
        self.assertFalse(species_not_produced)

        # ring with first reaction missing ->
        #   species_not_consumed = first reaction's reactant
        #   species_not_produced = first reaction's product
        for part in self.dfba_submodel.reactions[0].participants:
            if part.coefficient == -1:
                reactant = part.species
            if part.coefficient == 1:
                product = part.species
        del self.dfba_submodel.reactions[0]
        species_not_consumed, species_not_produced = model_analysis.get_dead_end_species(self.dfba_submodel, set())
        self.assertEqual(species_not_consumed.pop(), reactant)
        self.assertEqual(species_not_produced.pop(), product)
        self.assertFalse(species_not_consumed)
        self.assertFalse(species_not_produced)

        # make ring of 4 irreversible reactions
        self.create_reaction_network(self.dfba_submodel, 'ring', **{'num_rxn': 4, 'reversible': False})
        # ring with first reaction inactive ->
        #   species_not_consumed = first reaction's reactant
        #   species_not_produced = first reaction's product
        species_not_consumed, species_not_produced = model_analysis.get_dead_end_species(self.dfba_submodel,
                                                                                    set([self.dfba_submodel.reactions[0]]))
        self.assertEqual(species_not_consumed.pop(), reactant)
        self.assertEqual(species_not_produced.pop(), product)
        self.assertFalse(species_not_consumed)
        self.assertFalse(species_not_produced)

        # make ring of reversible reactions
        self.create_reaction_network(self.dfba_submodel, 'ring', **{'num_rxn': 3, 'reversible': True})
        # ring with first reaction missing -> all species produced and consumed
        del self.dfba_submodel.reactions[0]
        species_not_consumed, species_not_produced = model_analysis.get_dead_end_species(self.dfba_submodel, set())
        self.assertFalse(species_not_consumed)
        self.assertFalse(species_not_produced)

    def test_identify_dfba_submodel_rxn_gaps(self):
        model_analysis = self.model_analysis
        num_rxn = 4
        kwargs = {'num_rxn': num_rxn, 'reversible': False}
        # ring of 4 irreversible reactions -> no dead end species or inactive reactions
        self.create_reaction_network(self.dfba_submodel, 'ring', **kwargs)
        (not_consumed, not_produced), inactive_rxns = model_analysis.get_rxn_gaps(self.dfba_submodel)
        self.assertFalse(not_consumed)
        self.assertFalse(not_produced)
        self.assertFalse(inactive_rxns)

        # ring of 4 irreversible reactions with one missing -> all species dead end and all reactions inactive
        del self.dfba_submodel.reactions[0]
        (not_consumed, not_produced), inactive_rxns = model_analysis.get_rxn_gaps(self.dfba_submodel)
        species_in_ring = set(self.species[0:num_rxn])
        self.assertEqual(not_consumed, species_in_ring)
        self.assertEqual(not_produced, species_in_ring)
        self.assertEqual(sorted(inactive_rxns, key=lambda x: x.id),
                         sorted(self.dfba_submodel.reactions, key=lambda x: x.id))

    def test_digraph_of_rxn_network(self):
        self.run_test_on_digraph_of_rxn_network(5, False)

    def test_digraph_of_rxn_network_reversible(self):
        self.run_test_on_digraph_of_rxn_network(5, True)

    def run_test_on_digraph_of_rxn_network(self, num_rxn, reversible):
        self.create_reaction_network(self.dfba_submodel, 'ring', **{'num_rxn': num_rxn, 'reversible': reversible})
        g = self.model_analysis.get_digraph(self.dfba_submodel)

        for n in g.nodes():
            if isinstance(n, wc_lang.Reaction):
                self.assertTrue(self.RNX_ID_PREFIX in n.id)
            elif isinstance(n, wc_lang.Species):
                self.assertTrue(self.SPECIES_ID_PREFIX in n.id)

        # test expected vs. actual edges
        # expected edge id pairs
        expected_edges = set()
        # forward:
        for i in range(1, num_rxn+1):
            rxn_2_sp_edge = (self.rxn_id(i), self.sp_id((i % num_rxn)+1))
            expected_edges.add(rxn_2_sp_edge)
            sp_2_rxn_edge = (self.sp_id(i), self.rxn_id(i))
            expected_edges.add(sp_2_rxn_edge)
        if reversible:
            for i in range(1, num_rxn+1):
                rxn_2_sp_edge = (self.rxn_id(i), self.sp_id(i))
                expected_edges.add(rxn_2_sp_edge)
                sp_2_rxn_edge = (self.sp_id((i % num_rxn)+1), self.rxn_id(i))
                expected_edges.add(sp_2_rxn_edge)

        graph_edges = set()
        for s, d in g.edges():
            ids = []
            for n in [s, d]:
                if isinstance(n, wc_lang.Reaction):
                    ids.append(n.id)
                if isinstance(n, wc_lang.Species):
                    # remove compartment suffix '[some_comp]'
                    sp_type_id = n.id.split('[')[0]
                    ids.append(sp_type_id)
            s_id, d_id = ids
            graph_edges.add((s_id, d_id))
        self.assertEqual(expected_edges, graph_edges)

    def test_unbounded_paths(self):
        num_rxn = 8

        # irrreversible reactions
        # unbounded network
        self.create_reaction_network(self.dfba_submodel, 'ring', **{'num_rxn': num_rxn, 'reversible': False,
                                                                    'max_flux': float('inf')})
        path_len = 2*num_rxn-1
        g = self.model_analysis.get_digraph(self.dfba_submodel)
        paths = self.model_analysis.unbounded_paths(g, self.species[0], [self.species[num_rxn-1]])
        self.assertEqual(len(paths), 1)
        self.assertEqual(len(paths[0]), path_len)

        # bounded network
        self.create_reaction_network(self.dfba_submodel, 'ring', **{'num_rxn': num_rxn, 'reversible': False})
        g = self.model_analysis.get_digraph(self.dfba_submodel)
        paths = self.model_analysis.unbounded_paths(g, self.species[0],
                                                   [self.species[num_rxn-1]], min_non_finite_ub=self.default_max_flux+1)
        self.assertEqual(len(paths), 0)

        # reversible reactions, paths on both sides of ring
        # unbounded network
        self.create_reaction_network(self.dfba_submodel, 'ring', **{'num_rxn': num_rxn, 'reversible': True,
                                                                    'max_flux': float('inf')})
        g = self.model_analysis.get_digraph(self.dfba_submodel)
        paths = self.model_analysis.unbounded_paths(g, self.species[0], [self.species[num_rxn//2]])
        self.assertEqual(len(paths), 2)
        for p in paths:
            self.assertEqual(len(p), num_rxn+1)

        # bounded network
        self.create_reaction_network(self.dfba_submodel, 'ring', **{'num_rxn': num_rxn, 'reversible': True})
        g = self.model_analysis.get_digraph(self.dfba_submodel)
        paths = self.model_analysis.unbounded_paths(g, self.species[0], [self.species[num_rxn//2]],
                                                   min_non_finite_ub=self.default_max_flux+1)
        self.assertEqual(len(paths), 0)

        # test exceptions
        with self.assertRaisesRegex(ValueError, "'ex_species' should be a wc_lang.Species instance, but "):
            self.model_analysis.unbounded_paths(None, 'species', None)

        with self.assertRaisesRegex(ValueError, "elements of 'obj_fn_species' should be wc_lang.Species instances, but "):
            self.model_analysis.unbounded_paths(None, wc_lang.Species(), ['species'])

    def test_path_bounds_analysis(self):
        # read a wc model
        wc_lang.Submodel.objects.reset()
        wc_lang.Reaction.objects.reset()
        wc_lang.BiomassReaction.objects.reset()
        self.model = wc_lang.io.Reader().run(self.MODEL_FILENAME)
        self.dfba_submodel = wc_lang.Submodel.objects.get_one(id='submodel_1')
        self.model_analysis = wc_analysis.model.fba.FbaModelAnalysis(self.model)

        for rxn in self.dfba_submodel.reactions:
            rxn.max_flux = 0
        paths = self.model_analysis.path_bounds_analysis(self.dfba_submodel)
        for k in paths.keys():
            self.assertEqual(paths[k], [])

        for rxn in self.dfba_submodel.reactions:
            rxn.max_flux = float('inf')
        paths = self.model_analysis.path_bounds_analysis(self.dfba_submodel)
        self.assertEqual(len(paths['specie_1[e]']), 2)
