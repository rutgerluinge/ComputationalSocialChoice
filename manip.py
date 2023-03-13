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
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Literal,
    Optional,
    Set,
    Union,
)
import os
from copy import deepcopy
import STVComputations as stv
from STVComputations import Profile, all_alts
import itertools as itt
from tqdm import tqdm
from multiprocessing import Pool
from utils import aka, aka_or_name


ProfileList = List[Profile]
LinOrd = List[List[int]]
SCF = Callable[[List[Profile]], Set[int]]
Compared = Union[Literal[-1], Literal[0], Literal[1]]
BranchPruneFn = Callable[["ManipulatorConfig", int], bool]

# the comparator signature:
# a function that takes a profile, 2 outcomes (Set[int]) and the set of
# all alts (Set[int]) and returns -1/0/1 compared value

OutcomeComparator = Callable[[Profile, Set[int], Set[int], Set[int]], Compared]

# The manip generator factory signature
# NOTE: the
ManipGen = Callable[[ProfileList, LinOrd], Generator[LinOrd, None, None]]


# ==========================================
# Comparators


@aka("optim")
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


@aka("pessim")
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


@aka("perm")
def permut_manip_gen(_: ProfileList, o: LinOrd) -> Generator[LinOrd, None, None]:
    """
    A manipulated ballot generator that yields permutations of the original ballot.
    NOTE: therefore this generator will never mix alternatives into new linear order
    ties, i.e. if we have [[1],[2],[3]] this cannot generate orders such as [[1,2],[3]],
    it will only produce reordering of the given cells.

    NOTE: this ignores the overall profile list
    """
    for p in itt.permutations(o):
        yield list(p)


@aka("perm-all")
def all_permut_manip_gen(p: ProfileList, o: LinOrd) -> Generator[LinOrd, None, None]:
    """
    A manipulated ballot generator that yields all permutations of the full set of alternatives
    containes in the given ProfileList (i.e. of candidates in play)
    NOTE:
    NOTE: this ignores the actual linear order
    """
    alts = [[x] for x in stv.all_alts(p)]
    for perm in itt.permutations(alts):
        yield list(perm)


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

    # all alts is inferred if not specified
    all_alts: Set[int] = field(default_factory=set)

    minimal_n_stop: bool = True
    print_found: bool = False

    multiproc: bool = False

    branch_prune: Optional[BranchPruneFn] = None

    # the true outcome of the non-manip election, inferred
    true_outcome: Set[int] = field(init=False)

    def __post_init__(self):
        self.true_outcome = self.scf(self.trueballs)

        if not self.all_alts:
            self.all_alts = stv.all_alts(self.trueballs)

    def summary(self) -> str:
        return """\
trueballs\t=\t{}
scf\t=\t{}
comparator\t=\t{}
manip_gen\t=\t{}
true_outcome\t=\t{}
all_alts\t=\t{}
minimal_n_stop\t=\t{}
multiproc\t=\t{}
branch_prune\t=\t{}
""".format(
            stv.tot_votes(self.trueballs),
            aka_or_name(self.scf),
            aka_or_name(self.comparator),
            aka_or_name(self.manip_gen),
            self.true_outcome,
            self.all_alts,
            self.minimal_n_stop,
            0 if not self.multiproc else os.cpu_count(),
            aka_or_name(self.branch_prune),
        )


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

    @staticmethod
    def results_summary(results: List["ManipResult"]):
        n_from = len(list(itt.groupby(results, lambda x: x.from_ord)))
        n_to = len(list(itt.groupby(results, lambda x: x.to_ord)))
        n_from_to = len(list(itt.groupby(results, lambda x: (x.from_ord, x.to_ord))))

        return """\
count\t=\t{}
n_from\t=\t{}
n_to\t=\t{}
n_from_to\t=\t{}
""".format(
            len(results), n_from, n_to, n_from_to
        )


def test_manipulation(
    conf: ManipulatorConfig, i_coalition: int, manip_cand: LinOrd
) -> Generator[ManipResult, None, None]:
    """Test that under the given specification `conf` the i_th coalition
    could maniuplate the election by switching to `manip_cand` linear order
    instead of the truthful one.

    The process will try first with just 1 voter from the coalition switching, sequentially
    up to all memebers of the coalition switching to the new linear order.

    As soon as number of switchers results in a successful mainpulation it yields that
    scenario in the form of a ManipResult record. As such if you just care about A manipulation
    just call next once on the generator returned by this function, if you want all mainpulations
    call list on it.

    NOTE: when calling next, if no manipulation is possible a StopIteration
    exception is thrwon which you have to handle as a negative search result (no
    manip possible according to the manipulation scheme `conf` for the ith
    coalition). If calling list then a (possibly empty) list is returned and
    there is not error to handle in case of negative result.

    NOTE: if the manipulator config species `minimal_n_stop==True` then if a manipulation
    is found for some number of swithcers, no furter investigation for this coalition is
    pursued and the generator stop. Else the search contiues producing result also for higher
    number of switchers.

    """

    # given the truthful ballot of the ith coalition
    orig_coalition = conf.trueballs[i_coalition]

    # iterate on the number of switchers
    for n_manips in range(1, orig_coalition.count + 1):

        # ok now clone the List[Profiles] as this will be destructively modified
        new_balls = deepcopy(conf.trueballs)

        manip_p = Profile(manip_cand, n_manips)  # build manipulate profile

        # if n_manips is not all of the voters previously using this profile
        # the we need to keep some as before
        rest_p = None
        if n_manips < orig_coalition.count:
            rest_p = Profile(orig_coalition.ballot, orig_coalition.count - n_manips)

        # delete the from the cloned List[Profile] the working Profile

        del new_balls[i_coalition]

        new_balls.append(manip_p)  # add the manipulated profiles

        # if present add the rest of non-manip profiles i.e. voters from the
        # coalition that did not switch
        if rest_p:
            new_balls.append(rest_p)

        # check the new result according to our scf
        manip_outcome = conf.scf(new_balls)

        # use the comparator to see if this is positive result WRT to the coalition's original
        # preference order, the original outcome and the manipulated outcome under the comparator
        # specified in the scheme
        compar = conf.comparator(
            orig_coalition, conf.true_outcome, manip_outcome, conf.all_alts
        )

        if compar > 0:
            result = ManipResult(
                from_ord=orig_coalition.ballot,
                to_ord=manip_cand,
                n=n_manips,
                orig_outcome=conf.true_outcome,
                new_outcome=manip_outcome,
                new_votes=new_balls,
            )
            if conf.print_found:
                print("\n\nFound! -> ", result)
                pprint(result.new_votes)

            yield result

            # if minimal n stop will change manipulation
            # candidate if one is found for this order change. If not,
            # then say the for this candidate 2 switches are enough for the
            # manipulation to succeed, then 3,4,5 .. N will also be generated
            if conf.minimal_n_stop:
                break


# === utilities to parallelize the search


@dataclass
class ManipTask:
    conf: ManipulatorConfig
    i_coalition: int

    def __call__(self, x: LinOrd):
        # unfortunately we cannot return a generator
        # for tasks exectured in subprocess as it needs to be a picklable result
        # so in this case we must exhaustively search.
        # if conf.minimal_n_stop is true this is actually the same thing as
        # if there is a result then that is also the last result, if there is no result
        # then one hast to visti all search paths anyway
        return list(test_manipulation(self.conf, self.i_coalition, x))


def search_manips(conf: ManipulatorConfig, disable_progess=False):
    """
    Generator of search results.

    Implementation of the search problem described by the given config.
    """

    true_outcome = conf.scf(conf.trueballs)

    _all_alts = stv.all_alts(conf.trueballs)

    pool = Pool()

    with pool:
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

            # check if this branch should be skipped
            if conf.branch_prune and conf.branch_prune(conf, i_prof):
                continue

            cands = conf.manip_gen(conf.trueballs, p.ballot)

            dec_cands = tqdm(
                cands,
                desc=f"mid-{i_prof}",
                position=1,
                leave=False,
                disable=disable_progess,
            )

            # execute on a single processor
            if not conf.multiproc:
                for manip_cand in dec_cands:  # for each manipulation hypotesis
                    # if generator reuturns stuff then yield it
                    for result in test_manipulation(conf, i_prof, manip_cand):
                        yield result
            # execute on all available processors
            else:
                # build the task function/callable-object
                task = ManipTask(conf=conf, i_coalition=i_prof)
                # ran search along the manipulation hypoteses
                # in parallel
                for results in pool.imap(task, dec_cands):
                    if results:  # if the task returns something not empty
                        for r in results:  # then yield each result
                            yield r


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

    # NOTE: the above examples use the `permut_manip_gen`
    # as all voters already express a vote for each candidate
    # so it's equivalent to use `all_permut_manip_gen`
