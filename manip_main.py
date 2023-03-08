#!/usr/bin/env python3

from typing import Callable, List
import STVComputations as stv
from STVComputations import Profile
import manip
from pprint import pprint
import pickle
import os


ExpFactory = Callable[[List[Profile]], manip.ManipulatorConfig]

# We have several options to configure the search problem
# here i implemented pessimistic and optimistic manipulators
# with permuting hypotesis.
#
def stv_optimistic_permute_0(votes):
    return manip.ManipulatorConfig(
        votes,
        scf=stv.stv,
        comparator=manip.optimistic_comparator,
        manip_gen=manip.permut_manip_gen,
    )


def stv_pessimistic_permute_0(votes):
    return manip.ManipulatorConfig(
        votes,
        scf=stv.stv,
        comparator=manip.pessimistic_comparator,
        manip_gen=manip.permut_manip_gen,
    )


if __name__ == "__main__":
    # TODO: use argparse to set options here

    # * Load dataset *
    #
    # DATASET = "./dataset_revised.txt"
    #
    DATASET = "./dataset.txt"
    print(f"----- {DATASET} -----")
    votes = stv.extract_data(DATASET)

    # * Choose a search config *
    manip_conf_factory = stv_optimistic_permute_0

    # create the config for these votes
    confg_0 = manip_conf_factory(votes)

    # run search (list is required here because the search function returns a generator)
    results = list(manip.search_manips(confg_0))

    print(f"Found {len(results)} manipulations for {confg_0} on {DATASET} data")

    pprint(results)

    if len(results) > 0:
        with open(
            f"./results_{os.path.basename(DATASET)}-{manip_conf_factory.__name__}.pkl",
            "wb",
        ) as f:
            pickle.dump(results, f)
