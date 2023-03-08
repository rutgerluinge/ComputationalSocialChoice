from dataclasses import dataclass
from typing import List, Dict, Optional, Set
import re
import itertools
from copy import deepcopy, copy
from pprint import pprint


@dataclass
class Profile:
    """class to contain every row of data"""

    # [[1], [2], [3], [4,5], [6]]   : 1 > 2 > 3 > 4 = 5 > 6 (thats why 2d list)
    ballot: List[List[int]]
    count: int

    def alts(self) -> Set[int]:
        "Shortcut to get the set of alts in this Profile"
        return set(itertools.chain(*self.ballot))

    def rank_of(self, a: int) -> int:
        """get the rank of 'a' in lin-order cells.
        Returns len(ballot) for the top ranking,
        len(ballot) -1 for the second rank etc,
        last rank is 1. Not ranked is 0
        """
        n_cells = len(self.ballot)
        for i, cell in enumerate(self.ballot):
            if a in cell:
                return n_cells - i
        return 0


def all_alts(ps: List[Profile]) -> Set[int]:
    "Shortcut to get the overall set of alts in a list of Profile"
    alts = set()
    for p in ps:
        alts.update(p.alts())
    return alts


def format_ballot(ballot: str) -> list:
    """extract good format for ballot from a string"""

    my_list = []
    for x in re.findall(r"\d+|\{[^}]*\}", ballot):
        if "{" in x:
            sub_list = [int(y) for y in x.strip("{}").split(",")]
            my_list.append(sub_list)
        else:
            my_list.append([int(x)])

    return my_list


# def format_ballot(ballot: str) -> list[int]:
#     # @TODO i believe we can remove everything between {} as it states that the alternatives beteen the brackets are equally ranked, and every occasion happens at the end
#     ballot = ballot.strip()  # removes any whitespaces or newline characters
#
#     ballot = re.sub(r',{.*?}', '', ballot)  # removes everything between {} ,
#
#     ballot_str = ballot.split(',')  # make list
#
#     ballot_int = [int(x) for x in ballot_str]  # convert to int
#     return ballot_int


def line_extract(line: str) -> Profile:
    "Build Profile from `toi` text line"
    data_parts = line.split(":")  # split count from ballot
    count = int(data_parts[0])
    ballot = data_parts[1]
    ballot = format_ballot(ballot)
    return Profile(ballot, count)


def extract_data(path: str = "dataset_revised.txt") -> List[Profile]:
    """function to read and extract data from the dataset
    :return dictionary containing nr of votes as key, and ballot as value"""

    votes = list()
    with open(path, "r") as file:
        return [
            line_extract(line)
            for line in file
            if not line.startswith("#")
            or not line.strip()  # skip comments and empty lines
        ]


def plurality_round(
    votes: List[Profile], available_alternatives: Set[int]
) -> Dict[int, float]:
    """does 1 round of plurality, then returns a dictionary containing alternative:nr of votes (plurality)"""

    alternative_count = dict()
    for alternative in available_alternatives:
        alternative_count[alternative] = 0

    for profile in votes:
        # NOTE: we can do this version any way, still works if
        # len(profile.ballot[0]) == 1, then divisor is 1 and we add the simple count
        # if it's '{x,y,..}' case then we split the count equally
        for idx, alt in enumerate(profile.ballot[0]):
            alternative_count[profile.ballot[0][idx]] += profile.count * (
                1 / len(profile.ballot[0])
            )

        # TODO: remove if you agree with single implem
        # if len(profile.ballot[0]) == 1:  # should not be doing for [{x,y},z,w]
        #     alternative_count[profile.ballot[0][0]] += profile.count

        # if (
        #     len(profile.ballot[0]) > 1
        # ):  # in case [{1, 2}, 3, 4] -> both 1 and 2 should get 0.5 point per vote
        #     for idx, alt in enumerate(profile.ballot[0]):
        #         alternative_count[profile.ballot[0][idx]] += profile.count * (
        #             1 / len(profile.ballot[0])
        #         )
        # =====

    return alternative_count


def plurality(votes: List[Profile]) -> Set[int]:
    alts = all_alts(votes)
    p_scores = plurality_round(votes, alts)
    max_p = max(p_scores.values())
    return set([a for a in alts if p_scores[a] == max_p])


def remove_alternative(
    vote_profile: List[Profile], alternatives_to_remove: Set[int]
) -> List[Profile]:
    """Removes alts from the given alt set from all the given profiles.
    NOTE: makes in-place changes to the given profiles
    """

    for alternative in alternatives_to_remove:  # in case multiple
        # for each linear order
        for vote in vote_profile.copy():  # needs copy as we are removing from list
            # and every cell in it
            for alt_ballot in vote.ballot:  # this will almost always run once  {1,2}
                if (
                    alternative in alt_ballot
                ):  # CHECK if alternative matches ballot index
                    alt_ballot.remove(alternative)
                    # if nothing remains, then delete
                    if len(alt_ballot) == 0:
                        vote.ballot.remove(alt_ballot)

            # if the lin.order is left with 0 cells then delete
            if len(vote.ballot) == 0:  # remove empty ballots (no longer necessary)
                vote_profile.remove(vote)

    return vote_profile


def print_recap(
    p_scores: Dict[int, float], alternatives: Set[int], vote_round: int
) -> None:
    print(
        f"\t____________________________ vote round: {vote_round} ________________________________________\n"
        f"\tplurality scores: {p_scores}\n"
        f"\talternatives to be removed: {alternatives}\n"
        f"\t___________________________________________________________________________________\n"
    )


def stv_computations(votes: List[Profile], nr_of_alt: int, printing: bool) -> List[int]:
    """STV algorithm:
    - calculate plurality scores
    - remove alternative with lowest alternative score (in case of a tie remove both)
    @:return list of integers containing the winner(s) of the vote
    """
    all_alternatives = [x for x in range(1, nr_of_alt + 1)]  # hardcoded for now
    vote_round = 1

    while vote_round < 12:
        p_scores = plurality_round(
            votes=votes, available_alternatives=set(all_alternatives)
        )

        min_value = min(p_scores.values())
        alternatives = [key for key, value in p_scores.items() if value == min_value]

        if printing:
            print_recap(p_scores, set(alternatives), vote_round)

        votes = remove_alternative(
            vote_profile=votes, alternatives_to_remove=set(alternatives)
        )

        for alt in alternatives:
            all_alternatives.remove(alt)

        if len(alternatives) == len(p_scores):
            return alternatives

        vote_round += 1

    return [0]


def stv(votes: List[Profile], verbose: bool = False) -> Set[int]:
    """
    Slightly changed stv computation function.
    - Auto computes alternatives from the given List[Profile]
    - Does not modify the input objects, creates a deepcopy
    - Uses and returns sets instead of lists (should be faster too)
    - Loops untill all alts are removed and returns last non-empty alt-set instead of fixed # of rounds
    """

    full_alts = all_alts(votes)  # extract possible alternatives from ballots
    round = 1

    if verbose:
        print("STV start: init_alts =", full_alts)

    _alts_hist = []
    _votes = deepcopy(votes)  # don't modify original votes
    _alts = full_alts.copy()  # the working set of alts

    if not _alts:
        raise ValueError("There are no alternatives...")

    while _alts:  # as long as there are alternatives left

        _alts_hist.append(_alts.copy())  # store history of remaining alternatives

        p_scores = plurality_round(_votes, _alts)  # run plurality round

        min_value = min(p_scores.values())  # find minimal score
        # find alts with minimal score
        min_alts = set([k for k, v in p_scores.items() if v == min_value])

        remove_alternative(_votes, min_alts)

        _alts = _alts - min_alts  # remove the dropped alts

        if verbose:
            print_recap(p_scores, min_alts, round)
        round += 1

    if verbose:
        print("===== STV term, history: =====")
        pprint(_alts_hist)
        print("==============================")

    return _alts_hist[-1]


if __name__ == "__main__":
    # votes = extract_data()
    # print(f"winner: {stv_computations(votes, 11, printing=True)}")

    # votes0 = extract_data("./dataset.txt")
    # print(f"winner: {stv_computations(votes0, 5, printing=True)}")

    print("----- City council -----")
    votes = extract_data("./dataset_revised.txt")
    print("city-council winner:", stv(votes, verbose=True))

    print("\n\n----- Mayor -----")
    votes2 = extract_data("./dataset.txt")
    print("mayor winner:", stv(votes2, verbose=True))
