#!/usr/bin/env python3

from datetime import timedelta
import streamlit as st
import os
from export import load_result, load_summary, ResultsExporter, parse_time_delta
import configparser
import pandas as pd
import altair as alt

st.title("Manipulation results")

DIR = os.getenv("RESULTS_DIR") or "./results"


def main():
    dataset_name = st.selectbox("dataset", options=os.listdir(DIR))

    dataset_dir = os.path.join(DIR, dataset_name)
    schemes = os.listdir(dataset_dir)

    metas = {}

    summary_table = st.container()

    for scheme in sorted(schemes):
        scheme_dir = os.path.join(DIR, dataset_name, scheme)
        summary = load_summary(os.path.join(scheme_dir, ResultsExporter.summary_name))
        results = load_result(os.path.join(scheme_dir, ResultsExporter.pickle_name))

        summary_meta = configparser.ConfigParser()
        summary_meta.read_string(summary)
        metas[scheme] = summary_meta

        st.header(f"Scheme: {scheme} ({'NOT FOUND' if len(results)==0 else  'FOUND'})")

        st.markdown(f"```\n{summary}```")

        if len(results) > 0:
            for i, result in enumerate(results):
                with st.expander(
                    label=f"Manipulation on '{dataset_name}' with '{scheme}' [{i}]"
                ):
                    st.markdown(
                        """
                    - From: {}
                    - To: {}
                    - n: {}
                    - Original Outcome: {}
                    - New Outcome: {}
                    """.format(
                            result.from_ord,
                            result.to_ord,
                            result.n,
                            result.orig_outcome,
                            result.new_outcome,
                        )
                    )
                    st.markdown("#### New profile")
                    for p in result.new_votes:
                        st.write(p)
        else:
            st.warning("No manipulations found")

    ev_time_y = [parse_time_delta(m["execution"]["dur"]) for m in metas.values()]
    ev_time_x = list(metas.keys())
    ev_results = [m["results"]["count"] for m in metas.values()]

    time_df = pd.DataFrame(
        {
            "scheme": ev_time_x,
            "time": map(timedelta.total_seconds, ev_time_y),
            "manip_count": ev_results,
        }
    )

    with summary_table:
        st.write(time_df)

        chart = (
            alt.Chart(time_df)
            .mark_bar()
            .encode(
                alt.X("scheme"),
                alt.Y("time"),
                alt.Color("manip_count"),
                # alt.Tooltip(["Nucleotide", "Similarities"]),
            )
            .interactive()
        )
        st.altair_chart(chart)


main()
