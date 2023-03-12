from collections import OrderedDict
from typing import List, TypedDict
import STVComputations as stv
from STVComputations import Profile, stv_computations
import manip

import unittest


class TestBallotFormat(unittest.TestCase):
    """Test cases for parsing a comma-sep lin order into a List[List[int]]"""

    cases = {
        "basic": (
            "1,2,3,4",
            [[1], [2], [3], [4]],
        ),
        "tied_0": (
            "1,2,3,{4,5}",
            [[1], [2], [3], [4, 5]],
        ),
        "tied_1": (
            "{1,2},3,4,5",
            [[1, 2], [3], [4], [5]],
        ),
    }

    def test_format(self):
        for name, (inp, exp) in self.cases.items():
            out = stv.format_ballot(inp)
            self.assertListEqual(out, exp)


class TestProfileParsing(unittest.TestCase):

    lines = [
        "2: 1,2,3,4",
        "5: 1,2,3,{4,5}",
    ]

    outs = [
        Profile([[1], [2], [3], [4]], 2),
        Profile([[1], [2], [3], [4, 5]], 5),
    ]

    def test_parsing(self):
        for line, expected in zip(self.lines, self.outs):
            p = stv.line_extract(line)
            self.assertEqual(p, expected)


class TestPluralityRounds(unittest.TestCase):

    cases = {
        "simple": (
            [Profile([[1], [2], [3]], 3)],
            {
                1: 3,
                2: 0,
                3: 0,
            },
        ),
        "tied": (
            [
                Profile([[1], [2], [3]], 2),
                Profile([[2], [1], [3]], 2),
            ],
            {
                1: 2,
                2: 2,
                3: 0,
            },
        ),
        "split": (
            [Profile([[1, 2], [3]], 1)],
            {
                1: 0.5,
                2: 0.5,
                3: 0,
            },
        ),
    }

    def test_plur_round(self):
        for name, (profs, exp) in self.cases.items():
            alts = stv.all_alts(profs)
            res = stv.plurality_round(profs, alts)
            self.assertDictEqual(res, exp)


class TestRemoveAlts(unittest.TestCase):
    cases = {
        # basic case, deletes a lin order cell
        "a": {
            "from": [Profile([[1], [2]], 2)],
            "rm": {2},
            "out": [Profile([[1]], 2)],
        },
        # multiple case
        "b": {
            "from": [
                Profile([[1], [2, 3]], 3),
                Profile([[2, 3], [1]], 1),
            ],
            "rm": {2, 3},
            "out": [
                Profile([[1]], 3),
                Profile([[1]], 1),
            ],
        },
        # one in a tie
        "c": {
            "from": [Profile([[1], [2, 3]], 1)],
            "rm": {3},
            "out": [Profile([[1], [2]], 1)],
        },
        # elim lin ord completely
        "d": {
            "from": [
                Profile([[1], [2]], 1),
                Profile([[2]], 1),
            ],
            "rm": {2},
            "out": [Profile([[1]], 1)],
        },
    }

    def test_rm_alts(self):
        for name, spec in self.cases.items():
            votes = spec["from"]
            rm_alts = spec["rm"]
            expected = spec["out"]
            res = stv.remove_alternative(votes, rm_alts)
            self.assertEqual(res, expected)


class TestSTVCompute(unittest.TestCase):

    cases = {
        "simple": {
            "in": [Profile([[1], [2], [3], [4]], 10)],
            "out": {1},
        },
        "out_tie": {
            "in": [
                Profile([[1], [2], [3], [4]], 10),
                Profile([[2], [1], [3], [4]], 10),
            ],
            "out": {1, 2},
        },
        "lin_ord_equiv": {
            "in": [
                Profile([[1], [2], [3], [4]], 10),
                Profile([[2], [1], [3], [4]], 10),  # this would tie {1,2} as prev. case
                Profile([[3], [4, 2], [1]], 5),  # this breaks in favour of {2}
            ],
            "out": {2},
        },
        "lin_ord_eq_top": {
            "in": [
                Profile([[1], [3], [4]], 10),
                Profile([[2], [3], [4]], 10),  # this would tie {1,2} as prev. case
                Profile([[2, 3], [1], [4]], 10),  # this breaks in favour of {2}
            ],
            "out": {2},
        },
    }

    def test_stv(self):
        for name, spec in self.cases.items():
            inp = spec["in"]
            expected = spec["out"]
            res = stv.stv(inp)
            self.assertSetEqual(res, expected)

            # check consistency with prev implem
            p_res = stv.stv_computations(inp, len(stv.all_alts(inp)), printing=False)

            self.assertSetEqual(set(p_res), expected)


class TestSTVFromFile(unittest.TestCase):
    cases = {
        "city-council": {
            "file": "./data/city-council.txt",
            "expected": {8},
        },
        "mayor": {
            "file": "./data/mayor.txt",
            "expected": {4},
        },
    }

    def test_from_file(self):
        for name, spec in self.cases.items():
            votes = stv.extract_data(spec["file"])
            res = stv.stv(votes)

            self.assertSetEqual(res, spec["expected"])

            # check consistency with prev implem

            p_res = stv.stv_computations(
                votes, len(stv.all_alts(votes)), printing=False
            )

            self.assertSetEqual(set(p_res), spec["expected"])


## ---- Tests for the manip module ---


class TestOptimisticOutcomeComparatorProperties(unittest.TestCase):

    comparators: List[manip.OutcomeComparator] = [manip.optimistic_comparator]

    cases = OrderedDict(
        [
            (
                "pliny_example",
                {
                    # consider a voter with the following truthful profile
                    "trueballot": Profile([[3], [2], [1]], 1),
                    "outcomes": [
                        # ok new say the original outcome was {1}
                        # and the new one is {2}, then since
                        # 2 > 1 in the order, then this comparison should
                        # yield "+1" i.e. the voter is happier with the new outcome
                        {"orig": {1}, "new": {2}, "comp": 1},
                        {"orig": {1}, "new": {3}, "comp": 1},  # same here
                        # another example that should be indiff:
                        # an outcome is restricted to strictly prefrred one
                        # but optimistic only looks at max rank, so comp=0
                        {"orig": {2, 3}, "new": {3}, "comp": 0},
                        # this one is the opposite, the voter is worse off with this new result
                        {"orig": {3}, "new": {1}, "comp": -1},
                        {"orig": {2}, "new": {1}, "comp": -1},  # also here
                    ],
                },
            ),
            (
                "tied_ord_example",
                {
                    "trueballot": Profile([[4, 3], [2, 1]], 1),
                    "outcomes": [
                        {"orig": {1}, "new": {3}, "comp": 1},
                        # in this case indifference
                        {"orig": {3}, "new": {4}, "comp": 0},
                        {"orig": {3}, "new": {3, 4}, "comp": 0},
                        {"orig": {3, 4}, "new": {4}, "comp": 0},
                        # here we extend with a higher rank,
                        # max rank grows so comp=1
                        {"orig": {2}, "new": {3, 2}, "comp": 1},
                    ],
                },
            ),
            (
                "foreign_alts",
                {
                    "trueballot": Profile([[1], [2]], 1),
                    "outcomes": [
                        # voter is indiff to foreign alternatives
                        {"orig": {3}, "new": {4}, "comp": 0},
                        # voter is worse off with a foreig alt even WRT to lowest ranking
                        {"orig": {2}, "new": {3}, "comp": -1},
                    ],
                },
            ),
        ]
    )

    def test_props(self):

        for comp in self.comparators:  # for each comparator
            for name, spec in self.cases.items():  # for each scenario
                trueballot = spec["trueballot"]
                for i, outc in enumerate(
                    spec["outcomes"]  # type:ignore
                ):  # for each test-case-outcome
                    result = comp(
                        trueballot,  # type:ignore
                        outc["orig"],
                        outc["new"],
                        trueballot.alts(),  # type:ignore
                    )

                    self.assertEqual(
                        result,
                        outc["comp"],
                        f"Comparator [{comp}] fails test case: {name}['outcome'][{i}]",
                    )


class TestPessimisticOutcomeComparatorProperties(unittest.TestCase):

    comparators: List[manip.OutcomeComparator] = [manip.pessimistic_comparator]

    cases = OrderedDict(
        [
            (
                "pliny_example",
                {
                    # consider a voter with the following truthful profile
                    # NOTE: pessimistic look at the minimal rank
                    "trueballot": Profile([[3], [2], [1]], 1),
                    "outcomes": [
                        # these increase rank, so both ok, and same as optimistic
                        {"orig": {1}, "new": {2}, "comp": 1},
                        {"orig": {1}, "new": {3}, "comp": 1},  # same here
                        # here we differ from optimistic:
                        # the new alt has eliminated a low rank opt, so while optim was
                        # indifferent, pessimistc does prefer this outcome
                        # NOTE: difference with optimistic_comparator
                        {"orig": {2, 3}, "new": {3}, "comp": 1},
                        # this one is the opposite, the voter is worse off with this new result
                        {"orig": {3}, "new": {1}, "comp": -1},
                        {"orig": {2}, "new": {1}, "comp": -1},  # also here
                    ],
                },
            ),
            (
                "tied_ord_example",
                {
                    "trueballot": Profile([[4, 3], [2, 1]], 1),
                    "outcomes": [
                        {"orig": {1}, "new": {3}, "comp": 1},
                        # in this case indifference
                        {"orig": {3}, "new": {4}, "comp": 0},
                        {"orig": {3}, "new": {3, 4}, "comp": 0},
                        {"orig": {3, 4}, "new": {4}, "comp": 0},
                        # here we extend with a higher rank,
                        # max rank grows, but minrank stays the same,
                        # so pessitic is actually indiff to this change
                        # NOTE: diffrence with optimistic_comparator
                        {"orig": {2}, "new": {3, 2}, "comp": 0},
                    ],
                },
            ),
            (
                "foreign_alts",
                {
                    "trueballot": Profile([[1], [2]], 1),
                    "outcomes": [
                        # voter is indiff to foreign alternatives
                        {"orig": {3}, "new": {4}, "comp": 0},
                        # voter is worse off with a foreig alt even WRT to lowest ranking
                        {"orig": {2}, "new": {3}, "comp": -1},
                    ],
                },
            ),
        ]
    )

    def test_props(self):

        for comp in self.comparators:  # for each comparator
            for name, spec in self.cases.items():  # for each scenario
                trueballot = spec["trueballot"]
                for i, outc in enumerate(
                    spec["outcomes"]
                ):  # for each test-case-outcome
                    result = comp(
                        trueballot, outc["orig"], outc["new"], trueballot.alts()
                    )

                    self.assertEqual(
                        result,
                        outc["comp"],
                        f"Comparator [{comp}] fails test case: {name}['outcome'][{i}]",
                    )


class TestPlinyManipulation(unittest.TestCase):

    multiproc: bool = False

    orig_votes: List[Profile] = [
        Profile([[1], [2], [3]], 102),
        Profile([[2], [1], [3]], 101),
        Profile([[3], [2], [1]], 100),
    ]

    def test_canFindPlinyPluralityManip(self):

        # compute plurality vote for pliny scenario
        res = stv.plurality(self.orig_votes)

        self.assertEqual({1}, res)  # check original verdict is computed correctly

        # let's see if our implem can find the manipulation mentioned in the lecture notes

        # configure the search
        config = manip.ManipulatorConfig(
            trueballs=self.orig_votes,
            scf=stv.plurality,
            comparator=manip.pessimistic_comparator,
            manip_gen=manip.permut_manip_gen,
            multiproc=self.multiproc,
        )

        # get all manips
        manips = list(manip.search_manips(config, disable_progess=True))

        # check that at least a minpulation was found
        self.assertTrue(len(manips) > 0)

        # check that the manipulation c,b,a -> b,c,a
        # described in the lecture notes is found by our search alg
        self.assertTrue(
            any(
                map(
                    lambda m: m.from_ord == [[3], [2], [1]]
                    and m.to_ord == [[2], [3], [1]]
                    and m.new_outcome == {2},
                    manips,
                )
            )
        )


class TestPlinyManipulationParallel(unittest.TestCase):

    multiproc: bool = True

    orig_votes: List[Profile] = [
        Profile([[1], [2], [3]], 102),
        Profile([[2], [1], [3]], 101),
        Profile([[3], [2], [1]], 100),
    ]

    def test_canFindPlinyPluralityManip(self):

        # compute plurality vote for pliny scenario
        res = stv.plurality(self.orig_votes)

        self.assertEqual({1}, res)  # check original verdict is computed correctly

        # let's see if our implem can find the manipulation mentioned in the lecture notes

        # configure the search
        config = manip.ManipulatorConfig(
            trueballs=self.orig_votes,
            scf=stv.plurality,
            comparator=manip.pessimistic_comparator,
            manip_gen=manip.permut_manip_gen,
            multiproc=self.multiproc,
        )

        # get all manips
        manips = list(manip.search_manips(config, disable_progess=True))

        # print(manips)
        # check that at least a minpulation was found
        self.assertTrue(len(manips) > 0)

        # check that the manipulation c,b,a -> b,c,a
        # described in the lecture notes is found by our search alg
        self.assertTrue(
            any(
                map(
                    lambda m: m.from_ord == [[3], [2], [1]]
                    and m.to_ord == [[2], [3], [1]]
                    and m.new_outcome == {2},
                    manips,
                )
            )
        )


# class TestPlinyManipulation(TestPlinyManipulation):
#     multiproc = True


# def test_pliny():
#     # a -> 1
#     # b -> 2
#     # c -> 3
#     votes = [
#         Profile([[1], [2], [3]], 102),
#         Profile([[2], [1], [3]], 101),
#         Profile([[3], [2], [1]], 100),
#     ]

#     print(">>> truthfuls:")
#     plur_res = stv.plurality(votes)
#     print("Plur(pliny) =", plur_res)
#     stv_res = stv.stv(votes)
#     print("STV(pliny) =", stv_res)

#     votes_manip = [
#         Profile([[1], [2], [3]], 102),
#         Profile([[2], [1], [3]], 101),
#         Profile([[2], [3], [1]], 100),
#     ]

#     print(">>> maips:")
#     m_plur_res = stv.plurality(votes_manip)
#     print("Plur(m_pliny) =", m_plur_res)
#     m_stv_res = stv.stv(votes_manip)
#     print("STV(m_pliny) =", m_stv_res)


if __name__ == "__main__":
    unittest.main()
