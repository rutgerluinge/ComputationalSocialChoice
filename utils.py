#!/usr/bin/env python3

# import numba as nb
# from dataclasses import dataclass


# def jitdataclass(cls=None, *, extra_spec=[]):
#     """
#     Helper decorator to make it easier to numba jitclass dataclasses

#     Inspired by https://github.com/numba/numba/issues/4037#issuecomment-907523015
#     """

#     def _jitdataclass(cls):
#         dc_cls = dataclass(cls, eq=False, match_args=False)
#         del dc_cls.__dataclass_params__
#         del dc_cls.__dataclass_fields__
#         return nb.experimental.jitclass(dc_cls, spec=extra_spec)

#     if cls is not None:
#         # We've been called without additional args - invoke actual decorator immediately
#         return _jitdataclass(cls)
#     # We've been called with additional args - so return actual decorator which python calls for us
#     return _jitdataclass

from functools import wraps
from typing import Any, Optional


def aka(name: str):
    def dec(f):
        f.__aka__ = name
        return f

    return dec


def aka_or_name(v: Any) -> Optional[str]:
    if v is None:
        return "None"
    if hasattr(v, "__aka__"):
        return v.__aka__
    elif hasattr(v, "__name__"):
        return v.__name__
    return None
