# ComputationalSocialChoice

## Setup

### virtualenv

create and/or source your favourite virtualenv. 

I developed this project under python 3.10, but it was tested also in 3.8 and 3.9.


### deps

installer simply uses pip to install the requirements from `reqs.txt`:

`$ make install`

To check everything works run the tests

`$ make test`

In case changes require new depedencies then run

`$ make dump_deps` 

to refresh `reqs.txt`

## Implem

### STVComputations.py

Implements the core STV computations as well as data loading.

#### Data loading

Data can be loaded from txt files in "toi" via the `extract_data` format as follows

``` python
votes = extract_data("/path/to/dataset.txt")
```

The procedure returns a `List[Profile]` where Profile is the following data-strcuture:

``` python
@dataclass
class Profile:
    """class to contain every row of data"""

    # [[1], [2], [3], [4,5], [6]]   : 1 > 2 > 3 > 4 = 5 > 6 (thats why 2d list)
    ballot: List[List[int]]
    count: int
```

So in fact `Profile` is actually a single linear order (ballot) with an
attribute indicating how many times it was encountered.


#### STV SCF

In order to compute the STV SCF we have 2 helpers:

- `plurality_round(List[Profile], Set[int]) -> Dict[int, float]` that computes
  the plurality scores for the given `List[Profile]` with respect to the given
  alternatives `Set[int]`
  
- `remove_alternative(List[Profile], Set[int]) -> List[Profile]` that removes
  from the given `List[Profile]` the alternatives in `Set[int]`. Note that the
  function returns the `List[Profile]` but it actually mutates the Profile(s) in
  place, so one does not need to catch the return value
  
With the help of the above functions the actual SCF `stv(List[Profile]) -> Set[int]` can is implemented.
this makes a deep copy of the List[Profile] given, and then proceeds with the elimination of alternatives 
iteratively. At each round the plurality scores for each alternative are computed and then minimally scoring
alternatives are removed. Iteration stops once all alternatives are eliminated. The function returns the last 
non-empty set of alternatives as social choice.

Example usage:

``` python

votes2 = extract_data("./data/mayor.txt")
sc = stv(votes2, verbose=True)
print("mayor winner:", sc) # -> {4}

```


#### Tests

A test suite checking correctness properties of the implementation is given in `test_stv.py`

you can run the suite via `$ python test_stv.py` or `$ make test`



### Manipulating elections
We have 2 different methods to calculate whether an election is manipulable or not.
The first (STVManipulation.py).
#### STVManipulation.py
In this file we search for each alternative (x) whether it is possible to be elected above the original winner (y). This is done
to check for each ballot in the election, whether alternative x is ranked above y, if it is (or y doesn't exist in the ballot at all) 
then alternative x is swapped with the first choice of the ballot. As well as ranking the alternative y (if it exists) to the last index of the ballot.
These 2 swaps are both done to create more support for x and less suport for y, thus more chance for alternative x to survive a plurality round, and
for alternative y to *not* survive the alternative round

#### manip.py / manip_main.py /
premise:
- we have a set of Profile objects showing the original (truthful ballots)
- we have a scf:  `SCF = Callable[[List[Profile]], Set[int]]`
- we compute the results for truthful ballots
- we then implement a search problem that attempts to find the smallest group of voters
  that by submitting a modified version of their ballot can lead the final outcome to one that they prefer to the original one


implementation components:

**OutcomeComparator**

one thing we sure need is a comparison function that takes a Linear order and 2 outcomes
and returns:
  - (-1) iff the second outcome is worse thant the first WRT to the Linear order
  - (0) iff the 2 outcomes are indifferent
  - (1) iff the second outcome is better that the first WRT to the Linear order

the lecture notes indicate 2 manners of doing this comparison:
- optimistic -> compares max rank
- pessimistic -> compares min rank

The signature for such function is `OutcomeComparator = Callable[[Profile, Set[int], Set[int], Set[int]], Compared]` where `Compared` is the set of values [-1,0,1]


**ManipGen**
another component is a generator of manipulated linear orders:
given a linear order generates modifications of the order (by any conceivable procedure)
which will then be tested.

In practice we implement this a function which accepts a `List[Profile]` a and a `List[List[int]]` representing a linear order, and returns a generator of linear orders.

Signature: `ManipGen = Callable[[ProfileList, LinOrd], Generator[LinOrd, None, None]]`

Note that this means the manipulated order generator has access to the full set of
honest ballots besides the LinOrd of the manipulator.

We currently have 2 implementation of this function:
- **perm**: disregards the full set of profiles, returns permutations of the 
  original manipulator LinOrd (so results only contain the elements from the original order)
- **perm_all**: disregards the original manipulator's order, looks at the full set 
  of profiles to extract all candidates from there, returns all possible 
  linear orders without ties.
  
  
**extras**

Additional aspects of the search for manipulation are:

1. **minimal_n_stop**: Should the search stop investigating a branch once a result (for minimal number of switching voters) is found? For example in the Pliny case 2 switchers are sufficient.
2. **branch_prune**: a function to prune search branches. This is accounted for but not used yet.
3. **multiproc**: should the search use all available processors rather than just 1?
4. **all_alts**: if the profile does not contain some of the candidates (i.e. because zero voters expressed a preference for them), one can provide manually the set of alternatives. if not provided the set of alternatives is inferred from election data.

#### Putting it together

All of the aspects controlling the search are gathered in the following dataclass:

``` python
@dataclass
class ManipulatorConfig:
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
```

Once one has a properly configured `ManipulatorConfig` structure the search can be
ran via the `search_manips(conf: ManipulatorConfig)` function. By default this will show tqdm progress bar of the procedure. Time estimates are almost always wrong though becasue each coalition's time to compute may be very different, in particualr with the aspen dataset the first set of coalitions are large and so search takes longer, the following ones are progressively smaller so time per search iteration decreases

The `search_manpis` function returns the generator of (possible empty) manipulations found.

The generator returns objects of the following type:

``` python

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
```

#### Example usage

A couple of examples of the direct usage of the `search_manip` facility are given in the `__main__` block of `manip.py`.

For example the scenario from the roman senate given in the lecture notes can be reproduced as follows:

``` python
from STVComputations import Profile

plinyVotes = [
    Profile([[1], [2], [3]], 102),
    Profile([[2], [1], [3]], 101),
    Profile([[3], [2], [1]], 100),
]

from STVComputations import plurality
from manip import ManipulatorConfig, pessimistic_comparator, permut_manip_gen, search_manips

config_pessim = ManipulatorConfig(
    trueballs=plinyVotes,
    scf=plurality,
    comparator=pessimistic_comparator,
    manip_gen=permut_manip_gen,
)

from pprint import pprint

pprint(list(search_manips(config_pessim)))


```

With this produces the following output:

``` python
[ManipResult(from_ord=[[3], [2], [1]],
             to_ord=[[2], [3], [1]],
             n=2,
             orig_outcome={1},
             new_outcome={2},
             new_votes=[Profile(ballot=[[1], [2], [3]], count=102),
                        Profile(ballot=[[2], [1], [3]], count=101),
                        Profile(ballot=[[2], [3], [1]], count=2),
                        Profile(ballot=[[3], [2], [1]], count=98)]),
 ManipResult(from_ord=[[3], [2], [1]],
             to_ord=[[2], [1], [3]],
             n=2,
             orig_outcome={1},
             new_outcome={2},
             new_votes=[Profile(ballot=[[1], [2], [3]], count=102),
                        Profile(ballot=[[2], [1], [3]], count=101),
                        Profile(ballot=[[2], [1], [3]], count=2),
                        Profile(ballot=[[3], [2], [1]], count=98)])]
```

Which shows the [3,2,1] coalition can manipulate the election by just having 2 voters
switch to an unfaithful profile in 2 different ways, which have the same outcome: 
Instead of having 1 win the election, they manage to have 2 win the election, since they are pessimistic manipulators this is a successful manipulation because the minimal rank in the social choice has grown, from {1} -> third rank, to {2} -> second rank.

If one passed the `optimistic_comparator` that looks at the max rank instead, then a single switcher is sufficient:

``` python
[ManipResult(from_ord=[[3], [2], [1]],
             to_ord=[[2], [3], [1]],
             n=1,
             orig_outcome={1},
             new_outcome={1, 2},
             new_votes=[Profile(ballot=[[1], [2], [3]], count=102),
                        Profile(ballot=[[2], [1], [3]], count=101),
                        Profile(ballot=[[2], [3], [1]], count=1),
                        Profile(ballot=[[3], [2], [1]], count=99)]),
 ManipResult(from_ord=[[3], [2], [1]],
             to_ord=[[2], [1], [3]],
             n=1,
             orig_outcome={1},
             new_outcome={1, 2},
             new_votes=[Profile(ballot=[[1], [2], [3]], count=102),
                        Profile(ballot=[[2], [1], [3]], count=101),
                        Profile(ballot=[[2], [1], [3]], count=1),
                        Profile(ballot=[[3], [2], [1]], count=99)])]
```

In this case it's a tie, but the optimistic manipulator looks at the max rank which still grew from 3rd to 2nd by having 2 included in the tie.

## Running from command line with txt datasets

We provide a command line interface `manip_main.py` to systematically investigate scenarios.

``` text
Usage: manip_main.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  list-configs  list available schemes
  result        Inspect cached result
  results       Operate on results cache
  run           run a manipulation scheme
```

### Available configs

The combination of SCF, OutcomeComparator, ManipGen defines a configuration specification.
The available combinations can be listed via: `$ python manip_main.py list-configs`

available configurations:
	- plurality_optim_perm
	- plurality_optim_perm-all
	- plurality_pessim_perm
	- plurality_pessim_perm-all
	- stv_optim_perm
	- stv_optim_perm-all
	- stv_pessim_perm
	- stv_pessim_perm-all


### Running 

One or more configurations can be used against a given dataset to search for manipulations.
To do so use `run` command:

`$ python manip_main.py run --help`

``` text
Usage: manip_main.py run [OPTIONS]

  run a manipulation scheme

Options:
  -d, --dataset FILE              [required]
  -s, --spec [plurality_optim_perm|plurality_optim_perm-all|plurality_pessim_perm|plurality_pessim_perm-all|stv_optim_perm|stv_optim_perm-all|stv_pessim_perm|stv_pessim_perm-all|ALL]
                                  [required]
  -o, --out-dir DIRECTORY
  --multi / --no-multi
  --print-found / --no-print-found
  --stop-n / --no-stop-n
  --preview / --no-preview
  --force / --no-force
  --help                          Show this message and exit.

```

So one has to specify the path to the input data `-d` the name of the configuration spec to use `-s` (NOTE this can be passed multiple times or pass ALL as value to run all configs).

The rest of the options are optional, defaulting to:
- `-o ./results/`
- `--no-multi` (use `--multi` to use all available processors)
- `--no-print-found`
- `--stop-n`
- `--preview`
- `--no-force` (use `--force` to override cached results)

Example: run all configs on the roman senate 'pliny' dataset

`$ python manip_main.py run -d ./data/pliny.txt -s ALL`


### Results 
The script caches results on disk (by default in the `./results` dir). The `results` command operates on the cache (show cache or purge cache). 

The cache is organized by dataset at the first sudir level and by configuration identifier at the second level. Within the second level dir a pickle with the manipulation results is stored, as well as a metadata file which reports for example execution time. 

The `result` command allows inspection of a (deserialized) result set, one has to pass the path to the second level dir contain the result. 

Example: `$ python manip_main.py result --res-dir ./results/pliny/plurality_pessim_perm`

The command shows both results and metadata:

``` text
------ Viewing results from ./results/pliny/plurality_pessim_perm ------

==========================================
<Result 0>
ManipResult(from_ord=[[3], [2], [1]],
            to_ord=[[2], [3], [1]],
            n=2,
            orig_outcome={1},
            new_outcome={2},
            new_votes=[Profile(ballot=[[1], [2], [3]], count=102),
                       Profile(ballot=[[2], [1], [3]], count=101),
                       Profile(ballot=[[2], [3], [1]], count=2),
                       Profile(ballot=[[3], [2], [1]], count=98)])
<Result 1>
ManipResult(from_ord=[[3], [2], [1]],
            to_ord=[[2], [1], [3]],
            n=2,
            orig_outcome={1},
            new_outcome={2},
            new_votes=[Profile(ballot=[[1], [2], [3]], count=102),
                       Profile(ballot=[[2], [1], [3]], count=101),
                       Profile(ballot=[[2], [1], [3]], count=2),
                       Profile(ballot=[[3], [2], [1]], count=98)])
==========================================

[config]
trueballs	=	303
scf	=	plurality
comparator	=	pessim
manip_gen	=	perm
true_outcome	=	{1}
all_alts	=	{1, 2, 3}
minimal_n_stop	=	True
multiproc	=	0
branch_prune	=	None

[results]
count	=	2
n_from	=	1
n_to	=	2
n_from_to	=	2

[execution]
start	=	2023-03-12 17:06:23.822533
end	=	2023-03-12 17:06:23.878311
dur	=	0:00:00.055778
```

### Reproducing Aspen election results

Running all configs against the Aspen (Mayor) election data takes 46 minutes on my `CPU: Intel i5-7600K (4) @ 4.200GHz`. RAM is not really an issue here since with lazy generator based logic memory usage is fixed.

`$ python manip_main.py run -d ./data/mayor.txt -s ALL --multi`


## Exploring results (WIP)

A webgui for viewing results can be launched via

`make run_gui`

There you can select a dataset and the interface will list all results available in your cache
for that dataset. To use a different cache dir than default point it with the following env var: `RESULTS_DIR=/path/to/the/dir` before running the make script. 

For example to use the sample results i commited into the repo use 

`$ RESULTS_DIR=sample_results make run_gui`


