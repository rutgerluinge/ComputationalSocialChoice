# ComputationalSocialChoice

## Setup

### virtualenv

create and/or source your favourite virtualenv

### deps

`pip install -r reqs.txt`

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

votes2 = extract_data("./dataset.txt")
sc = stv(votes2, verbose=True)
print("mayor winner:", sc) # -> {4}

```


#### Tests

A test suite checking correctness properties of the implementation is given in `test_stv.py`

you can run the suite via `python test_stv.py`


### Manipulating elections

WORK IN PROGRESS

I introduced a module `manip.py` that sets up infrastructure for a manipulation serch problem.
The current manipulation hypothesis generation procedure seems to not be enough... but
we still have some time to figure this out. See the module for some documentation/ideas of my implementation.

`manip_main.py` is an example of running such procedure


## NOTES

