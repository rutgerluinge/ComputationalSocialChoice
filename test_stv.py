import STVComputations as stv
from STVComputations import Profile, stv_computations

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
            "file": "./dataset_revised.txt",
            "expected": {8},
        },
        "mayor": {
            "file": "./dataset.txt",
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


if __name__ == "__main__":
    unittest.main()
