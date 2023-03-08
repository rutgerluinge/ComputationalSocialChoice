#!/usr/bin/env python3
"""
Generating vote manipulations

concepts:
- we have a set of Profile objects showing the original (truthful ballots)
- we have an scf
- we compute the results for truthful ballots
- we then implement a search problem that attempts to find the smallest group of voters
  that by submitting a modifyied version of their ballot can lead the final outcome to one that they prefer
  to the original one


implem components:

### 1 OutcomeComparator
one thing we sure need is a comparison function that takes a Linear order and 2 outcomes
and returns:
  - (-1) if the second outcome is worse thant the first WRT to the Linear order
  - (0) if the 2 outcomes are indiff
  - (1) iif the second outcome is better that the first WRT to the Linear order

the lecture notes indicate 2 manners of doing this comparison:
- optimistic -> compares max rank
- pessimistic -> compares min rank

### 2 ManipGen
another component is a generator of manipulated linear orders:
given a linear order generates modifications of the order (by any conceivable procedure)
which will then be tested.

apporach we actually specify a factory function from linear order to generator of linear orders

### 3
by means of composition we will combine an scf, a comparator and a candidate


A test case:
From the lecture notes we have an example where Plurarlity is manipulable (see test_pliny in test test_stv.py)
"""
from pprint import pprint
from dataclasses import dataclass, field
from typing import Callable, Dict, Generator, Iterable, List, Literal, Set
from copy import deepcopy
import STVComputations as stv
from STVComputations import Profile
import itertools as itt
from tqdm import tqdm


ProfileList = List[Profile]
LinOrd = List[List[int]]
SCF = Callable[[List[Profile]], Set[int]]
Compared = Literal[-1] | Literal[0] | Literal[1]

# the comparator signature:
# a function that takes a profile, 2 outcomes (Set[int]) and the set of
# all alts (Set[int]) and returns -1/0/1 compared value

OutcomeComparator = Callable[[Profile, Set[int], Set[int], Set[int]], Compared]

# The manip generator factory signature
# NOTE: the
ManipGen = Callable[[ProfileList, LinOrd], Generator[LinOrd, None, None]]


# ==========================================
# Comparators


def optimistic_comparator(
    p: Profile, out_a: Set[int], out_b: Set[int], alts: Set[int]
) -> Compared:
    """Optimistic manipulator comparison op.
    Optimistic comparison looks at the max rank in the first and second outcome,
    it orders based on the max rank
    :return: the comparison -1/0/+1 of the max ranks

    """

    # compute max_rank for each outcome:
    # rank 0 is assigned to foreign alts (i.e. those not expressed by the given Profile)
    max_rank_a = max([p.rank_of(a) for a in out_a])
    max_rank_b = max([p.rank_of(a) for a in out_b])

    if max_rank_b > max_rank_a:
        return 1  # secon outcome preferred
    elif max_rank_b < max_rank_a:
        return -1  # first outcome preferred
    return 0  # indifference


def pessimistic_comparator(
    p: Profile, out_a: Set[int], out_b: Set[int], alts: Set[int]
) -> Compared:
    """Pessimistic manipulator comparison op.
    Pess. comparison looks at the min rank in the first and second outcome,
    it orders based on the min rank
    :return: the comparison -1/0/+1 of the min ranks

    """

    # compute max_rank for each outcome:
    # rank 0 is assigned to foreign alts (i.e. those not expressed by the given Profile)
    min_rank_a = min([p.rank_of(a) for a in out_a])
    min_rank_b = min([p.rank_of(a) for a in out_b])

    if min_rank_b > min_rank_a:
        return 1  # secon outcome preferred
    elif min_rank_b < min_rank_a:
        return -1  # first outcome preferred
    return 0  # indifference


# ==========================================
# Manip Generators


def permut_manip_gen(_: ProfileList, o: LinOrd) -> Generator[LinOrd, None, None]:
    """
    A manipulated ballot list than yields permutations of the original ballot.
    NOTE: therefore this generator will never mix alternatives into new linear order
    ties, i.e. if we have [[1],[2],[3]] this cannot generate orders such as [[1,2],[3]],
    it will only produce reordering of the given cells.

    NOTE: this ignores the overall profile list
    """
    for p in itt.permutations(o):
        yield list(p)


# ==========================================
# Search alg implem


@dataclass
class ManipulatorConfig:
    """
    The configuration structure for the manipulation search problem.

    It specifies the orginal (truthful) ballots,
    the SCF to use, a comparator strategy for outcomes, and
    a manipulation candidate generator factory.

    There are 2 dimensions in the search space:
    1. the manipulated ballot, how is the ballot manipulated
    2. how many voters switch from truthful to strategic ballot?
    Hence additionally one can indicate wether to stop at first successful manipulation
    with respect to some manip ballot. If true (default) then the search along a particular
    strategic ballot branch will stop at the first (if any) number of voters that satisfies
    the search criteria (comparator -> 1), rather than continue with more strategic switchers

    """

    trueballs: List[Profile] = field(repr=False)
    scf: SCF
    comparator: OutcomeComparator
    manip_gen: ManipGen

    minimal_n_stop: bool = True


@dataclass
class ManipResult:
    """The data structure yieled by successful search iterations.

    It specifies the original linear order being manipulated,
    the manipulated orders, how many voters switched, the original and new outcome,
    and the complete manipulated List[Profile].

    NOTE: in the new List[Profile] the maniuplated Profile entry will be split
    in 2 new entries (1 if all the voters of that original profile line
    switched). If the manip row happens to be the same as one of the other truthfuls
    those will not be merged, so we'll have 2 Profile in the List with the same .ballot

    """

    from_ord: LinOrd
    to_ord: LinOrd
    n: int
    orig_outcome: Set[int]
    new_outcome: Set[int]
    new_votes: List[Profile]


def search_manips(conf: ManipulatorConfig, disable_progess=False):
    """
    Generator of search results.

    Implementation of the search problem described by the given config.

    NOTE: this is a naive implementation with no particular optimizations/heuristics

    """

    true_outcome = conf.scf(conf.trueballs)

    _all_alts = stv.all_alts(conf.trueballs)

    # ok so now for each linear order in the list of Profile
    # we want to check if by strategic voting we can get a better outcome for this
    # profile
    for i_prof, p in tqdm(
        enumerate(conf.trueballs),
        desc="outer (coalition)",
        position=0,
        total=len(conf.trueballs),
        disable=disable_progess,
    ):
        # generate candidate manipulations

        # === NOTE HACK ===
        # this is just a HACK to avoid huge permutation lists for now, otherwise it may
        # take hours to complete
        # this for the 5 alts problem this is never the case clearly,
        # for the 11 alts the factorial behind premutations explodes fast after 6.
        # maybe bruteforcing permutations is not the way...
        ##
        # if len(p.ballot) > 6:
        #     print("!!!!>>>> skipping large ballot: len=", len(p.ballot))
        #     continue

        cands = conf.manip_gen(conf.trueballs, p.ballot)

        for manip_cand in tqdm(
            cands,
            desc=f"mid-{i_prof}",
            position=1,
            leave=False,
            disable=disable_progess,
        ):
            # we start with a single 1 changing profile, up to
            # all of them changing profile
            for n_manips in range(1, p.count + 1):

                # ok now clone the List[Profiles]
                new_balls = deepcopy(conf.trueballs)

                # build a new Profile for the manipulators
                manip_p = Profile(manip_cand, n_manips)

                # if n_manips is not all of the voters previously using this profile
                # the we need to keep some as before
                rest_p = None
                if n_manips < p.count:
                    rest_p = Profile(p.ballot, p.count - n_manips)

                # delete the from the clones List[Profile] the working Profile

                del new_balls[i_prof]

                # add the manipulated profiles
                new_balls.append(manip_p)

                # if present add the rest of non-manip profiles
                if rest_p:
                    new_balls.append(rest_p)

                manip_outcome = conf.scf(new_balls)

                compar = conf.comparator(p, true_outcome, manip_outcome, _all_alts)

                if compar > 0:
                    # print("<<<", p.ballot, "->", manip_cand, f"[{n_manips}]")
                    # we found a successfull manuipulation
                    # print("!")
                    yield ManipResult(
                        from_ord=p.ballot,
                        to_ord=manip_cand,
                        n=n_manips,
                        orig_outcome=true_outcome,
                        new_outcome=manip_outcome,
                        new_votes=new_balls,
                    )

                    # if minimal n stop will change manipulation
                    # candidate if one is found for this order change. If not,
                    # then say the for this candidate 2 switches are enough for the
                    # manipulation to succeed, then 3,4,5 .. N will also be generated
                    if conf.minimal_n_stop:
                        break


if __name__ == "__main__":

    # run manipulation search on the pliny scenario

    plinyVotes = [
        Profile([[1], [2], [3]], 102),
        Profile([[2], [1], [3]], 101),
        Profile([[3], [2], [1]], 100),
    ]

    # 1. with plurality scf and optimistic manip
    config_optim = ManipulatorConfig(
        trueballs=plinyVotes,
        scf=stv.plurality,
        comparator=optimistic_comparator,
        manip_gen=permut_manip_gen,
    )

    m_res = next(search_manips(config_optim))
    print("Plurality+optim -> First manipulation found:", m_res)
    pprint(m_res.new_votes)

    print("\n\n" + 42 * "=")
    # 2. with plurality scf and pessimistic manip
    config_pessim = ManipulatorConfig(
        trueballs=plinyVotes,
        scf=stv.plurality,
        comparator=pessimistic_comparator,
        manip_gen=permut_manip_gen,
    )

    m_res_pess = next(search_manips(config_pessim))
    print("Plurality+pessim -> First manipulation found:", m_res_pess)
    pprint(m_res_pess.new_votes)

    print("\n\n" + 42 * "=")
    # 3. with stv scf and pessim manip
    confg_pessim_stv = ManipulatorConfig(
        trueballs=plinyVotes,
        scf=stv.stv,
        comparator=pessimistic_comparator,
        manip_gen=permut_manip_gen,
    )

    try:
        m_res_stv_pess = next(search_manips(confg_pessim_stv))
        print("STV+pessim -> First manip found:", m_res_stv_pess)
        pprint(m_res_stv_pess.new_votes)
    except StopIteration:
        print("STV+pessim -> Could not find a satisfying manip")

    print("\n\n" + 42 * "=")
    # 4. with stv scf and optim manip
    confg_optim_stv = ManipulatorConfig(
        trueballs=plinyVotes,
        scf=stv.stv,
        comparator=optimistic_comparator,
        manip_gen=permut_manip_gen,
    )

    try:
        m_res_stv_optim = next(search_manips(confg_optim_stv))
        print("STV+optim -> First manip found:", m_res_stv_optim)
        pprint(m_res_stv_optim.new_votes)
    except StopIteration:
        print("STV+optim -> Could not find a satisfying manip")

    # NOTE: the above examples stop search at the first match
    # to go further call multiple times next on the generator
    # or coerce/iterate the generator
