#!/usr/bin/env python3

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List
import manip
import pickle
import os


@dataclass
class ExecInfo:
    start: datetime
    end: datetime

    @property
    def dur(self):
        return self.end - self.start

    def summary(self) -> str:
        return """\
start\t=\t{}
end\t=\t{}
dur\t=\t{}
""".format(
            self.start, self.end, self.dur
        )


@dataclass
class ResultsExporter:
    """Helper class to manage results disk-caching.
    Stores results in the following hierarchy within `out_dir`:
    - <dataset_name>
      - <alg_name>
        - <pickle_name>
        - <summary_name>
    """

    out_dir: str

    pickle_name: str = "results.pkl"
    summary_name: str = "summary.ini"

    def _save_results(self, path: str, results: List[manip.ManipResult]):
        with open(path, "wb") as f:
            pickle.dump(results, f)

    def _save_summary(
        self,
        path: str,
        config: manip.ManipulatorConfig,
        results: List[manip.ManipResult],
        info: ExecInfo,
    ):
        summary = """\
[config]
{}
[results]
{}
[execution]
{}
""".format(
            config.summary(),
            manip.ManipResult.results_summary(results),
            info.summary(),
        )

        with open(path, "w") as f:
            f.write(summary)

    def _dir_for(self, dataset: str, spec: str, config: manip.ManipulatorConfig):
        dataset_name, _ = os.path.splitext(os.path.basename(dataset))
        dataset_dir = os.path.join(self.out_dir, dataset_name)
        alg_dir = f"{spec}{'__no-stop-n' if not config.minimal_n_stop else ''}"
        return os.path.join(dataset_dir, alg_dir)

    def result_exists(self, dataset: str, spec: str, config: manip.ManipulatorConfig):
        the_dir = self._dir_for(dataset, spec, config)
        return os.path.exists(the_dir)

    def __call__(
        self,
        dataset: str,
        spec: str,
        config: manip.ManipulatorConfig,
        results: List[manip.ManipResult],
        info: ExecInfo,
    ):
        the_dir = self._dir_for(dataset, spec, config)

        os.makedirs(the_dir, exist_ok=True)
        pickle_path = os.path.join(the_dir, self.pickle_name)
        summary_path = os.path.join(the_dir, self.summary_name)
        self._save_results(pickle_path, results)
        self._save_summary(summary_path, config, results, info)


def load_result(from_path: str) -> List[manip.ManipResult]:
    with open(from_path, "rb") as fi:
        return pickle.load(fi)


def load_summary(from_path: str) -> str:
    with open(from_path, "r") as fi:
        return fi.read()


def parse_time_delta(s: str):
    hms = s.split(":")
    return timedelta(hours=int(hms[0]), minutes=int(hms[1]), seconds=float(hms[2]))
