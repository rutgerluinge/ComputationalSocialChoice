#!/usr/bin/env python3
from typing import Any, List
import STVComputations as stv
import manip
from peu.core import dict_product
from utils import aka_or_name


def config_name(conf: dict):
    parts = []
    for _k in ["scf", "comparator", "manip_gen"]:
        v = conf[_k]
        _aka = aka_or_name(v)
        if _aka is None:
            raise Exception(f"Config item {_k}:{v} has no dunder aka or name")
        parts.append(_aka)
    return "_".join(parts)


def gen_configs(options: dict):
    combs = dict_product(options)
    return {config_name(v): v for v in combs}


# define the options
options = {
    "scf": [stv.stv, stv.plurality],
    "comparator": [manip.optimistic_comparator, manip.pessimistic_comparator],
    "manip_gen": [manip.permut_manip_gen, manip.all_permut_manip_gen],
}

# generate configs
configs = gen_configs(options)


def spec_to_ManipulatorConfig(spec: dict, votes: List[stv.Profile], **kwargs):
    return manip.ManipulatorConfig(trueballs=votes, **spec, **kwargs)
