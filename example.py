#!/usr/bin/env python3


from STVComputations import Profile

plinyVotes = [
    Profile([[1], [2], [3]], 102),
    Profile([[2], [1], [3]], 101),
    Profile([[3], [2], [1]], 100),
]

from STVComputations import plurality
from manip import (
    ManipulatorConfig,
    pessimistic_comparator,
    optimistic_comparator,
    permut_manip_gen,
    search_manips,
)

config_pessim = ManipulatorConfig(
    trueballs=plinyVotes,
    scf=plurality,
    # comparator=pessimistic_comparator,
    comparator=optimistic_comparator,
    manip_gen=permut_manip_gen,
)

from pprint import pprint

pprint(list(search_manips(config_pessim)))
