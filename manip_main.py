#!/usr/bin/env python3
"""
CLI entry point to run the project.

"""
import configparser
from typing import Callable, List
import STVComputations as stv
from STVComputations import Profile
import manip
from pprint import pprint
import pickle
import os
import click
from configs import configs, spec_to_ManipulatorConfig
from datetime import datetime
from dataclasses import dataclass
from export import ExecInfo, ResultsExporter, load_result, load_summary
import seedir
import shutil

from utils import aka_or_name


def preview_results(results: List[manip.ManipResult]):
    if len(results) > 0:
        print()
        print("=" * 42)
        for i, r in enumerate(results):
            print(f"<Result {i}>")
            pprint(r)
        print("=" * 42)
        print()
    else:
        print("---- No manipulations found ----")


@click.group()
def cli():
    ...


# === Search running ===
@cli.command(help="run a manipulation scheme")
@click.option(
    "-d",
    "--dataset",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
)
@click.option(
    "-s",
    "--spec",
    type=click.Choice(list(configs.keys()) + ["ALL"]),
    required=True,
    multiple=True,
)
@click.option(
    "-o",
    "--out-dir",
    type=click.Path(file_okay=False, dir_okay=True),
    default="./results",
)
@click.option("--multi/--no-multi", default=False)
@click.option("--print-found/--no-print-found", default=False)
@click.option("--stop-n/--no-stop-n", default=True)
@click.option("--preview/--no-preview", default=True)
@click.option("--force/--no-force", default=False)
def run(dataset, spec, out_dir, multi, print_found, stop_n, preview, force):

    exporter = ResultsExporter(out_dir)

    click.echo(f"Running manipulator search, dataset: {dataset}\nSelected specs:")
    for i, s in enumerate(spec):
        print(f"\t- {i}: {s}")

    # load the dataset
    try:
        votes = stv.extract_data(dataset)
    except Exception as e:
        raise click.ClickException(f"Could not load dataset [{dataset}] {e}")

    # ok now determine the list of specs to run
    # if --spec ALL was present the run all specs
    _specs = list(configs.keys()) if "ALL" in spec else spec

    ran = []
    skipped = []

    for _spec in _specs:
        i_spec = len(ran) + len(skipped)
        # determine the configuration spec
        manip_spec = configs[_spec]

        click.echo(f"\n>>> configuration {i_spec}:")
        for k, v in manip_spec.items():
            print(f"\t- {k}: {aka_or_name(v) or v}")
        print()

        # instantiate the config
        manip_config = spec_to_ManipulatorConfig(manip_spec, votes)

        # configure additional options
        manip_config.multiproc = multi
        manip_config.print_found = print_found
        manip_config.minimal_n_stop = stop_n

        # Check if result was already computed
        if exporter.result_exists(dataset, _spec, manip_config) and not force:
            skipped.append(_spec)
            continue

        # Preamble
        click.echo(
            f"> Original outcome according to config: {manip_config.true_outcome}\n"
        )
        click.echo("> Running search...")

        start = datetime.now()
        # run
        results = list(manip.search_manips(manip_config))
        end = datetime.now()

        click.echo(f"Found {len(results)} manipulations for {_spec} on {dataset} data")

        # export results
        exporter(dataset, _spec, manip_config, results, ExecInfo(start, end))

        # preview results
        if len(results) > 0 and preview:
            preview_results(results)

        ran.append(_spec)

    print("-" * 21, "SUMMARY", "-" * 21)
    if ran:
        print(f"Ran {len(ran)} specs:")
        for s in ran:
            print("\t-", s)

    if skipped:
        print(f"Skipped {len(skipped)} specs:")
        for s in skipped:
            print("\t-", s)

        print("\trun with '--force' to overwrite")
    print("-" * 51)


# === Results management ===
@cli.command(help="Operate on results cache")
@click.option(
    "-o",
    "--out-dir",
    type=click.Path(file_okay=False, dir_okay=True),
    default="./results",
)
@click.option("--tree", "action", flag_value="tree")
@click.option("--clean-all", "action", flag_value="clean")
def results(out_dir, action):
    if action == "tree":
        seedir.seedir(path=out_dir)
    elif action == "clean":
        click.confirm(
            "Are you SURE you want to delete the results dir?",
            default=False,
            abort=True,
        )
        click.echo("OK, deleting results dir")
        shutil.rmtree(out_dir)


@cli.command(help="Inspect cached result")
@click.option("--res-dir", type=click.Path(file_okay=False, dir_okay=True, exists=True))
def result(res_dir):

    click.echo(f"------ Viewing results from {res_dir} ------")

    res_pickle = os.path.join(res_dir, ResultsExporter.pickle_name)
    res_summary = os.path.join(res_dir, ResultsExporter.summary_name)

    summary = load_summary(res_summary)

    manip_results: List[manip.ManipResult] = load_result(res_pickle)

    preview_results(manip_results)

    print(summary)


# === Info ===


@cli.command(help="list available schemes")
def list_configs():
    click.echo("Listing available configurations:")
    for k in configs:
        print("\t-", k)


if __name__ == "__main__":
    cli()
