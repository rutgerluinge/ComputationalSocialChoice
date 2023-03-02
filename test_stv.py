from STVComputations import Profile, stv_computations

def test_simple_case():
    votes = []

    votes.append(Profile([[1], [2], [3], [4]], 10))

    assert stv_computations(votes=votes, nr_of_alt=4, printing=False) == [1]


def test_simple_tie_case():
    votes = []

    votes.append(Profile([[1], [2], [3], [4]], 10))
    votes.append(Profile([[2], [1], [3], [4]], 10))

    assert stv_computations(votes=votes, nr_of_alt=4, printing=False) == [1, 2]


def test_square_bracket():
    votes = []

    votes.append(Profile([[1], [2], [3], [4]], 10))
    votes.append(Profile([[2], [1], [3], [4]], 10))
    votes.append(Profile([[3], [4, 2], [1]], 5))

    assert stv_computations(votes=votes, nr_of_alt=4, printing=False) == [2]


def test_tie_as_top_vote():
    votes = []
    votes.append(Profile([[1], [3], [4]], 10))
    votes.append(Profile([[2], [3], [4]], 10))
    votes.append(Profile([[2, 3], [1], [4]], 10))

    assert stv_computations(votes=votes, nr_of_alt=4, printing=True) == [2]
