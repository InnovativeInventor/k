from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyk.cterm import CSubst
from pyk.kast.inner import KVariable, Subst
from pyk.kcfg import KCFG
from pyk.kcfg.semantics import DefaultSemantics
from pyk.prelude.kint import geInt, intToken, ltInt
from pyk.prelude.ml import mlAnd, mlEqualsTrue, mlOr
from pyk.utils import single

from ..test_kcfg import node_dicts, propagate_split_constraints, split_dicts, x_config, x_subst

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pyk.cterm import CTerm

x_lt_0 = mlEqualsTrue(ltInt(KVariable('X'), intToken(0)))
x_ge_0 = mlEqualsTrue(geInt(KVariable('X'), intToken(0)))
x_lt_3 = mlEqualsTrue(ltInt(KVariable('X'), intToken(3)))
x_ge_3 = mlEqualsTrue(geInt(KVariable('X'), intToken(3)))
x_lt_4 = mlEqualsTrue(ltInt(KVariable('X'), intToken(4)))
x_ge_4 = mlEqualsTrue(geInt(KVariable('X'), intToken(4)))
x_lt_5 = mlEqualsTrue(ltInt(KVariable('X'), intToken(5)))
x_ge_5 = mlEqualsTrue(geInt(KVariable('X'), intToken(5)))


def test_simple_merge_node() -> None:
    simple_semantics = TestSemantics()
    original_cfg = merge_node_test_kcfg()
    original_cfg.merge_nodes(simple_semantics)
    assert original_cfg.to_dict() == merge_node_test_kcfg_simple_expected().to_dict()


class TestSemantics(DefaultSemantics):
    def is_mergeable(self, c1: CTerm, c2: CTerm) -> bool:
        return True


def merge_node_test_kcfg() -> KCFG:
    """
    1 -|Split: X >=Int 5|->            2 -|Edge: (5, (r1), #Top)|->                                                        6
      -|Split: X >=Int 3 & X <Int 5|-> 3 -|Edge: (10, (r2,r3), X >=Int 4 & X <Int 5), (15, (r4), X <Int 4 & X >=Int 3 )|-> 7
      -|Split: X >=Int 0 & X <Int 3|-> 4 -|Edge: (20, (r5), #Top)|->                                                       8
      -|Split: X  <Int 0|->            5 -|Edge: (25, (r6), #Top)|->                                                       9
    #Top: CSubst()
    """
    d = {
        'next': 10,
        'nodes': node_dicts(9, config=x_config()),
        'edges': edge_dicts(
            (2, 6, [5], [['r1']], [CSubst()]),
            (3, 7, [10, 15], [['r2', 'r3'], ['r4']], [x_subst().add_constraint(x_ge_4).add_constraint(x_lt_5), x_subst().add_constraint(x_ge_3).add_constraint(x_lt_4)]),
            (4, 8, [20], [['r5']], [CSubst()]),
            (5, 9, [25], [['r6']], [CSubst()]),
        ),
        'splits': split_dicts((1, [(2, x_ge_5), (3, mlAnd([x_ge_3, x_lt_5])), (4, mlAnd([x_ge_0, x_lt_3])), (5, x_lt_0)]), csubst=x_subst()),
    }
    cfg = KCFG.from_dict(d)
    propagate_split_constraints(cfg)
    return cfg


def merge_node_test_kcfg_simple_expected() -> KCFG:
    """
    1 -|Edge: (5, (r1), X >=Int 5),
              (10, (r2,r3), X >=Int 4 & X <Int 5),
              (15, (r4), X <Int 4 & X >=Int 3 ),
              (20, (r5), X >=Int 0 & X <Int 3),
              (25, (r6), X <Int 0)|
      -> 6 | 7 | 8 | 9
      -|Split: X >=Int 5|->            6
      -|Split: X >=Int 3 & X <Int 5|-> 7
      -|Split: X >=Int 0 & X <Int 3|-> 8
      -|Split: X  <Int 0|->            9
    """
    d = {
        'next': 12,
        'nodes': node_dicts(11, config=x_config()),
        'edges': edge_dicts(
            (1, 11, [5, 10, 15, 20, 25], [['r1'], ['r2', 'r3'], ['r4'], ['r5'], ['r6']],
             [x_subst().add_constraint(x_ge_5),
              x_subst().add_constraint(x_ge_4).add_constraint(x_lt_5).add_constraint(x_ge_3),
              x_subst().add_constraint(x_ge_3).add_constraint(x_lt_4).add_constraint(x_lt_5),
              x_subst().add_constraint(x_lt_3).add_constraint(x_ge_0),
              x_subst().add_constraint(x_lt_0)])
        ),
        'splits': split_dicts((11, [(6, x_ge_5), (7, mlAnd([x_ge_3, x_lt_5])), (8, mlAnd([x_ge_0, x_lt_3])), (9, x_lt_0)]), csubst=x_subst()),
    }
    cfg = KCFG.from_dict(d)
    propagate_split_constraints(cfg)
    cfg.remove_node(2)
    cfg.remove_node(3)
    cfg.remove_node(4)
    cfg.remove_node(5)
    cfg.remove_node(10)
    return cfg


# class TestSemanticsComplex(DefaultSemantics):
#     def is_mergeable(self, c1: CTerm, c2: CTerm) -> bool:
#         """
#         X >=Int 0 mergeable
#         X <Int 5 mergeable
#         """
#         if len(c1.constraints) == 0 or len(c2.constraints) == 0:
#             return False
#
#         x = x_subst()
#         a = x.add_constraint(x_lt_0)
#         b = x.add_constraint(x_ge_0_lt_3)
#         c = x.add_constraint(x_ge_3_lt_5)
#         d = x.add_constraint(x_ge_5)
#
#         def _ge0(ct: CTerm) -> bool:
#             return ct.constraints == b.constraints or ct.constraints == c.constraints or ct.constraints == d.constraints
#
#         def _lt5(ct: CTerm) -> bool:
#             return ct.constraints == a.constraints or ct.constraints == b.constraints or ct.constraints == c.constraints
#
#         return (_ge0(c1) and _ge0(c2)) or (_lt5(c1) and _lt5(c2))


# def merge_node_test_kcfg_complex_expected(cfg: KCFG) -> None:
#     """
#     1 -|Split: X >=Int 0|-> 2 | 3 | 4 -|Edge: (5, (r1), X >=Int 5),
#                                               (10, (r2,r3), X >=Int 4 & X <Int 5), (15, (r4), X <Int 4 & X >=Int 3 ),
#                                               (20, (r5), X >=Int 0 & X <Int 3),|-> 6 | 7 | 8 -|Split|-> 6 , 7 , 8
#       -|Split: X <Int 5|-> 3 | 4 | 5 -|Edge: (10, (r2,r3), X >=Int 4 & X <Int 5), (15, (r4), X <Int 4 & X >=Int 3 ),
#                                              (20, (r5), X >=Int 0 & X <Int 3),
#                                              (25, (r6), X <Int 0)|-> 7 | 8 | 9 -|Split|-> 7 , 8 , 9
#     """
#     _1_to_splits = single(cfg.splits(source_id=1))
#     splits = _1_to_splits.splits
#     assert len(splits) == 2
#     for split_node_id in splits:
#         constraints = single(splits[split_node_id].constraints)
#         edge = single(cfg.edges(source_id=split_node_id))
#         if constraints == mlOr([mlOr([x_ge_3_lt_5, x_ge_0_lt_3]), x_ge_5]):
#             assert (5, ('r1',), x_subst().add_constraint(x_ge_5)) in edge.info
#             assert (
#                 10,
#                 ('r2', 'r3'),
#                 x_subst().add_constraint(x_ge_4).add_constraint(x_lt_5).add_constraint(x_ge_3),
#             ) in edge.info
#             assert (
#                 15,
#                 ('r4',),
#                 x_subst().add_constraint(x_ge_3).add_constraint(x_lt_4).add_constraint(x_lt_5),
#             ) in edge.info
#             assert (20, ('r5',), x_subst().add_constraint(x_lt_3).add_constraint(x_ge_0)) in edge.info
#             end_split = single(cfg.splits(source_id=edge.target.id)).splits
#             assert end_split[6] == x_subst().add_constraint(x_ge_5)
#             assert end_split[7] == x_subst().add_constraint(x_lt_5).add_constraint(x_ge_3)
#             assert end_split[8] == x_subst().add_constraint(x_lt_3).add_constraint(x_ge_0)
#         elif constraints == mlOr([mlOr([x_ge_3_lt_5, x_ge_0_lt_3]), x_lt_0]):
#             # constraints == x_lt_5
#             assert (
#                 10,
#                 ('r2', 'r3'),
#                 x_subst().add_constraint(x_ge_4).add_constraint(x_lt_5).add_constraint(x_ge_3),
#             ) in edge.info
#             assert (
#                 15,
#                 ('r4',),
#                 x_subst().add_constraint(x_ge_3).add_constraint(x_lt_4).add_constraint(x_lt_5),
#             ) in edge.info
#             assert (20, ('r5',), x_subst().add_constraint(x_lt_3).add_constraint(x_ge_0)) in edge.info
#             assert (25, ('r6',), x_subst().add_constraint(x_lt_0)) in edge.info
#             end_split = single(cfg.splits(source_id=edge.target.id)).splits
#             assert end_split[7] == x_subst().add_constraint(x_lt_5).add_constraint(x_ge_3)
#             assert end_split[8] == x_subst().add_constraint(x_lt_3).add_constraint(x_ge_0)
#             assert end_split[9] == x_subst().add_constraint(x_lt_0)
#         else:
#             AssertionError(f'Unexpected constraints: {constraints}')
#
#
# def test_merge_node() -> None:
#     simple_semantics = TestSemantics()
#     original_cfg = merge_node_test_kcfg()
#     original_cfg.merge_nodes(simple_semantics)
#     assert original_cfg.to_dict() == merge_node_test_kcfg_simple_expected().to_dict()
#
#     # # for complex heuristics
#     # complex_semantics = TestSemanticsComplex()
#     # original_cfg = merge_node_test_kcfg()
#     # original_cfg.merge_nodes(complex_semantics)
#     # merge_node_test_kcfg_complex_expected(original_cfg)


def edge_dicts(*edges: Iterable) -> list[dict[str, Any]]:
    def _make_edge_dict(i: int, j: int,
                        depths: Iterable[int],
                        rules_list: Iterable[Iterable[str]],
                        csubsts: Iterable[CSubst]
                        ) -> dict[str, Any]:
        return {
            'source': i,
            'target': j,
            'depths': list(depths),
            'rules_list': [list(rules) for rules in rules_list],
            'csubsts': [csubst.to_dict() for csubst in csubsts],
        }

    return [_make_edge_dict(*edge) for edge in edges]



