from STVComputations import Profile, remove_alternative, stv_computations, manipulate_ballot_1
from copy import deepcopy

def test_simple_case():
    votes = []

    votes.append(Profile([[1], [2], [3], [4]], 10))

    assert stv_computations(votes=votes, nr_of_alt=4) == [1]


def test_simple_tie_case():
    votes = []

    votes.append(Profile([[1], [2], [3], [4]], 10))
    votes.append(Profile([[2], [1], [3], [4]], 10))

    assert stv_computations(votes=votes, nr_of_alt=4) == [1, 2]


def test_square_bracket():
    votes = []

    votes.append(Profile([[1], [2], [3], [4]], 10))
    votes.append(Profile([[2], [1], [3], [4]], 10))
    votes.append(Profile([[3], [4, 2], [1]], 5))

    assert stv_computations(votes=votes, nr_of_alt=4) == [2]

def test_simple_manipulation():
    votes = []
    """these votes below should be manipulable as 3 voters dislike alternative 1, and as it seems now they are losing"""
    votes.append(Profile([[1], [2], [3], [4]], 10))
    votes.append(Profile([[2], [3], [4], [1]], 4))
    votes.append(Profile([[3], [4], [2], [1]], 4))
    votes.append(Profile([[4], [2], [3], [1]], 4))
    votes_copy = deepcopy(votes)
    assert stv_computations(votes=votes, nr_of_alt=4) == [1]

    manipulate_ballot_1(profiles=votes_copy, winner_alternative=1, wished_alternative=2)

    assert stv_computations(votes=votes_copy, nr_of_alt=4) == [2]



