import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="CurST-Net++ Project Dashboard",
    page_icon="🚦",
    layout="wide",
)

PRIMARY = {"PEMS03": "#2E86AB", "PEMS04": "#E67E22", "PEMS08": "#27AE60"}

# ----------------------------------------------------------------------------
# DATA (from the project's final results, checkpoints, and logs)
# ----------------------------------------------------------------------------
stages = ["Stage 0", "Stage 1", "Stage 2", "Stage 3"]
stage_labels = {
    "Stage 0": "Baseline reproduction",
    "Stage 1": "+ Traffic-Aware Positional Encoding",
    "Stage 2": "+ Gated IRSM",
    "Stage 3": "+ Dynamic Curriculum + Learnable Fusion",
}

results = {
    "PEMS03": {
        "nodes": 358, "samples": 26208, "period": "09/2018-11/2018",
        "paper_mae": 15.19,
        "mae": [19.27, 19.07, 19.04, 19.08],
        "rmse": [None, 33.61, 33.64, 33.78],
        "mape": [None, 17.32, 17.37, 17.29],
        "delta": [None, 1.05, 0.19, -0.23],
        "note": "Stage 0 baseline retuned from ω=1.0 (19.42) to ω=0.6 (19.27), adopted as reference.",
    },
    "PEMS04": {
        "nodes": 307, "samples": 16992, "period": "01/2018-02/2018",
        "paper_mae": 19.22,
        "mae": [22.93, 22.44, 22.33, 22.35],
        "rmse": [None, 38.39, 38.30, 38.37],
        "mape": [None, 14.55, 14.45, 14.49],
        "delta": [None, 2.12, 0.49, -0.07],
        "note": "Main pipeline dataset; Stages 1-3 validated here first before extending to PEMS03/08.",
    },
    "PEMS08": {
        "nodes": 170, "samples": 17856, "period": "07/2016-08/2016",
        "paper_mae": 15.50,
        "mae": [21.86, 21.41, 21.36, 21.29],
        "rmse": [None, 37.55, 37.52, 37.87],
        "mape": [None, 13.33, 13.22, 13.16],
        "delta": [None, 2.06, 0.24, 0.31],
        "note": "Only dataset where Stage 3 gave a genuine improvement; Gated IRSM used init_omega=0.9 workaround.",
    },
}

datasets = list(results.keys())

bugs = [
    ("NB0 data setup", "os.makedirs ran before checking the shared Drive folder existed, silently creating a duplicate in Shanjay's own Drive.", "Fail-loud pre-flight existence check."),
    ("MAPE metric", "Naive clamp(min=1e-3) produced nonsensical values (48,000%+) on near-zero traffic-flow points.", "Excluded near-zero true-flow points from the MAPE average."),
    ("Training loop", "No gradient clipping or LR decay, contributing to Stage 0 baselines being 19-45% worse than the paper initially.", "Added gradient clipping and LR decay."),
    ("Curriculum epoch bug", "Extending epochs on an already-graduated model re-locked it to a restricted node subset using the new epoch count as denominator (hit Shanjay's PEMS03 run).", "Decoupled curriculum_epochs (fixed) from extendable total epochs."),
    ("Checkpointing", "Only 'latest' weights were saved, so a later-epoch regression could overwrite the best weights.", "Track and save best_model_state separately, protected from overwrite."),
    ("Stage 1 extension notebooks", "PEMS03/PEMS08 notebooks had leftover hardcoded DATASET='PEMS04', causing node-count mismatches.", "Fixed and verified DATASET string per notebook."),
    ("Stage 3 GPU bug", "CPU-only EMA loss state mixed with GPU tensors after checkpoint resume and in static difficulty computation.", "Found via Srihari's Colab GPU run; fixed in both locations."),
    ("Gated IRSM range", "Sigmoid gate only represents ω in (0,1); PEMS08's paper-tuned ω is 1.4 (out of range).", "Used init_omega=0.9 as a documented compromise for PEMS08."),
    ("Stage 3 early stop", "Srihari's PEMS04 run early-stopped at epoch 17, before the curriculum ramp (epoch 20) or blending (epoch 30) fully activated.", "Bumped patience 15→35 so training resumes past epoch 30 before judging."),
]

# ----------------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------------
st.sidebar.title("🚦 CurST-Net++")
st.sidebar.caption("Research project dashboard")
page = st.sidebar.radio(
    "Section",
    ["Overview", "Stage Results", "Cross-Dataset Analysis", "Bugs Fixed", "Team & Files"],
)
st.sidebar.divider()
st.sidebar.markdown(
    "**Goal:** beat *CurST-Net* (Chen et al., IEEE TSMC 2026) on PEMS03/04/08, "
    "or failing that, show a documented relative-improvement story."
)
st.sidebar.markdown("**Status:** ✅ All experimental work complete — paper in progress.")

# ----------------------------------------------------------------------------
# OVERVIEW
# ----------------------------------------------------------------------------
if page == "Overview":
    st.title("CurST-Net++ — Project Overview")
    st.markdown(
        "Extending *CurST-Net* with three learnable, additive modules — "
        "traffic-aware positional encoding, Gated Interlayer Residual Scaling, and a "
        "dynamic curriculum with learnable difficulty fusion — validated against the "
        "reproduced baseline and evaluated cumulatively across three PEMS benchmarks."
    )

    st.subheader("Final metrics (Stage 3)")
    cols = st.columns(3)
    for c, ds in zip(cols, datasets):
        r = results[ds]
        final_mae = r["mae"][-1]
        gain = (r["mae"][0] - final_mae) / r["mae"][0] * 100
        with c:
            st.metric(
                label=f"{ds}  ({r['nodes']} nodes)",
                value=f"MAE {final_mae:.2f}",
                delta=f"{gain:+.2f}% vs Stage 0",
            )
            st.caption(f"RMSE {r['rmse'][-1]:.2f}  ·  MAPE {r['mape'][-1]:.2f}%")
            st.caption(f"Paper-reported MAE: {r['paper_mae']:.2f}")

    st.divider()
    st.subheader("MAE progression across all stages")
    fig = go.Figure()
    for ds in datasets:
        fig.add_trace(go.Scatter(
            x=stages, y=results[ds]["mae"], mode="lines+markers", name=ds,
            line=dict(color=PRIMARY[ds], width=3), marker=dict(size=9),
        ))
    fig.update_layout(
        yaxis_title="MAE", xaxis_title="", height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(t=30, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "**Key finding:** Traffic-Aware PE (Stage 1) and Gated IRSM (Stage 2) improved MAE "
        "consistently on all 3 datasets. Stage 3 (Dynamic Curriculum + Learnable Fusion) helped "
        "PEMS08 (+0.31%) but was flat/slightly negative on PEMS04 (-0.07%) and PEMS03 (-0.23%) — "
        "a genuine dataset-dependent effect, not a broken module (0-1% rank agreement with the "
        "static baseline confirmed the mechanism was active in all three runs)."
    )

# ----------------------------------------------------------------------------
# STAGE RESULTS
# ----------------------------------------------------------------------------
elif page == "Stage Results":
    st.title("Stage-by-Stage Results")
    ds = st.selectbox("Dataset", datasets)
    r = results[ds]

    st.caption(f"{r['nodes']} nodes · {r['samples']:,} samples · {r['period']} · Caltrans PeMS, SF Bay Area")
    if r["note"]:
        st.warning(r["note"])

    df = pd.DataFrame({
        "Stage": [f"{s} — {stage_labels[s]}" for s in stages],
        "MAE": r["mae"],
        "RMSE": r["rmse"],
        "MAPE (%)": r["mape"],
        "Δ vs prior stage (%)": r["delta"],
    })
    st.dataframe(df, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            x=stages, y=r["mae"], color=stages,
            labels={"x": "", "y": "MAE"}, title=f"{ds} — MAE by stage",
        )
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = go.Figure(go.Bar(
            x=["This work (Stage 0)", "Paper-reported [1]"],
            y=[r["mae"][0], r["paper_mae"]],
            marker_color=[PRIMARY[ds], "#B0B0B0"],
        ))
        fig2.update_layout(title=f"{ds} — Reproduction vs. paper", yaxis_title="MAE", height=380)
        st.plotly_chart(fig2, use_container_width=True)

# ----------------------------------------------------------------------------
# CROSS-DATASET ANALYSIS
# ----------------------------------------------------------------------------
elif page == "Cross-Dataset Analysis":
    st.title("Cross-Dataset Analysis")

    metric = st.radio("Metric", ["MAE", "RMSE", "MAPE"], horizontal=True)
    key = metric.lower()
    fig = go.Figure()
    for ds in datasets:
        vals = results[ds][key]
        fig.add_trace(go.Scatter(
            x=stages, y=vals, mode="lines+markers", name=ds,
            line=dict(color=PRIMARY[ds], width=3),
        ))
    fig.update_layout(yaxis_title=metric, height=420)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Total improvement, Stage 0 → Stage 3")
    gains = [(ds, (results[ds]["mae"][0] - results[ds]["mae"][-1]) / results[ds]["mae"][0] * 100) for ds in datasets]
    gdf = pd.DataFrame(gains, columns=["Dataset", "Total MAE gain (%)"])
    fig3 = px.bar(gdf, x="Dataset", y="Total MAE gain (%)", color="Dataset",
                  color_discrete_map=PRIMARY, text_auto=".2f")
    fig3.update_layout(showlegend=False, height=360)
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Gap to original paper (absolute MAE)")
    gap = [(ds, (results[ds]["mae"][-1] - results[ds]["paper_mae"]) / results[ds]["paper_mae"] * 100) for ds in datasets]
    gapdf = pd.DataFrame(gap, columns=["Dataset", "Gap vs paper (%)"])
    st.dataframe(gapdf.style.format({"Gap vs paper (%)": "{:.1f}%"}), use_container_width=True, hide_index=True)
    st.caption(
        "Absolute MAE remains above the original paper's reported figures on all three datasets — "
        "attributed to not reproducing the base paper's full per-dataset hyperparameter search, "
        "not a flaw in the proposed extensions."
    )

# ----------------------------------------------------------------------------
# BUGS FIXED
# ----------------------------------------------------------------------------
elif page == "Bugs Fixed":
    st.title("Bugs Found & Fixed")
    st.caption("For context on any weird-looking checkpoints, results, or logs.")
    for where, problem, fix in bugs:
        with st.expander(f"🐛 {where}"):
            st.markdown(f"**Problem:** {problem}")
            st.markdown(f"**Fix:** {fix}")

# ----------------------------------------------------------------------------
# TEAM & FILES
# ----------------------------------------------------------------------------
elif page == "Team & Files":
    st.title("Team, Constraints & Files")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Team")
        st.markdown(
            "- **Rocky** — lead, ~1 hr/day, last-resort for tasks\n"
            "- **Srihari, Shanjay, Mitesh** — 3-5 hr/day each\n"
            "- Laptop sessions capped at 3 continuous hours\n"
            "- Task assignments rotate per stage — not fixed to one dataset per person"
        )
    with c2:
        st.subheader("Infra")
        st.markdown(
            "- Shared Google Drive folder **CurST-Net++** (Editor access, all 4)\n"
            "- Subfolders: `data/`, `checkpoints/`, `results/`, `logs/`\n"
            "- Self-contained Colab notebooks — multiple people can run different notebooks at once"
        )

    st.divider()
    st.subheader("Notebook naming convention")
    st.markdown(
        "- `NB0` — data setup (one-time, shared)\n"
        "- `NB1a/b/c` — Stage 0 baseline, PEMS03/04/08\n"
        "- `NB1a-retune` — PEMS03 ω=0.6 retune (adopted baseline)\n"
        "- `NB2_Stage1_TrafficAwarePE_{DATASET}` — Stage 1, all 3 complete\n"
        "- `NB3_Stage2_GatedIRSM_{DATASET}` — Stage 2, all 3 complete\n"
        "- `NB4_Stage3_DynamicCurriculum_{DATASET}` — Stage 3, all 3 complete\n"
        "- Checkpoints: `stageN_{DATASET}.pt` · Results: `stageN_{DATASET}_metrics.json`"
    )

    st.subheader("Checkpoints available in Drive")
    ckpts = []
    for ds in datasets:
        for s in range(4):
            ckpts.append(f"stage{s}_{ds}.pt")
    st.dataframe(pd.DataFrame({"checkpoint": ckpts}), use_container_width=True, hide_index=True, height=200)

st.sidebar.divider()
st.sidebar.caption("Data source: project results JSON files (Stage 0-3, PEMS03/04/08).")
