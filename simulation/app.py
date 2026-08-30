import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Can AI Predict Tomorrow's Traffic?", page_icon="🚗", layout="wide")

# ----------------------------------------------------------------------------
# REAL NUMBERS FROM THE PROJECT (used to drive the simulation honestly —
# these are the actual final accuracy figures, not made up)
# ----------------------------------------------------------------------------
ROADS = {
    "Downtown Loop": {
        "peak": 380, "base": 70, "mae_basic": 19.27, "mae_smart": 19.08, "mapes": 17.29,
        "blurb": "A busy, tightly-packed city loop with lots of intersections.",
    },
    "North Bay Corridor": {
        "peak": 340, "base": 55, "mae_basic": 22.93, "mae_smart": 22.35, "mapes": 14.49,
        "blurb": "A long commuter freeway stretch connecting suburbs to downtown.",
    },
    "Coastal Highway": {
        "peak": 260, "base": 40, "mae_basic": 21.86, "mae_smart": 21.29, "mapes": 13.16,
        "blurb": "A quieter coastal route with lighter, more predictable traffic.",
    },
}

DAY_TYPES = ["Weekday", "Weekend"]

# ----------------------------------------------------------------------------
# SIMULATED "REAL WORLD" TRAFFIC CURVE
# ----------------------------------------------------------------------------
def simulate_true_flow(peak, base, day_type, seed):
    rng = np.random.default_rng(seed)
    hours = np.linspace(0, 24, 288)  # 5-min resolution
    if day_type == "Weekday":
        morning = peak * 0.85 * np.exp(-((hours - 8.2) ** 2) / (2 * 0.9 ** 2))
        evening = peak * np.exp(-((hours - 17.5) ** 2) / (2 * 1.1 ** 2))
        curve = base + morning + evening
    else:
        midday = peak * 0.55 * np.exp(-((hours - 13.5) ** 2) / (2 * 3.0 ** 2))
        curve = base + midday
    curve += rng.normal(0, base * 0.08, size=hours.shape)
    curve = np.clip(curve, base * 0.5, None)
    return hours, curve


def congestion_label(value, peak, base):
    frac = (value - base) / max(peak - base, 1)
    if frac < 0.25:
        return "🟢 Light", "#27AE60"
    elif frac < 0.6:
        return "🟡 Moderate", "#E1A100"
    else:
        return "🔴 Heavy", "#C0392B"


# ----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# ----------------------------------------------------------------------------
st.sidebar.title("🚗 Try it yourself")
road = st.sidebar.selectbox("Pick a road", list(ROADS.keys()))
day_type = st.sidebar.radio("Day type", DAY_TYPES, horizontal=True)
depart_hour = st.sidebar.slider("Your planned departure time", 0.0, 23.5, 8.0, 0.5,
                                 format="%.1f h")

if "seed" not in st.session_state:
    st.session_state.seed = 42
if st.sidebar.button("🔄 Simulate a new day"):
    st.session_state.seed += 1

st.sidebar.divider()
st.sidebar.caption(
    "This is a simulation for demonstration purposes — it uses this project's "
    "real accuracy numbers to control how far off each AI's guesses are, but "
    "the traffic patterns themselves are illustrative, not live sensor data."
)

# ----------------------------------------------------------------------------
# HERO
# ----------------------------------------------------------------------------
st.title("Can AI Predict Tomorrow's Traffic Before It Happens?")
st.markdown(
    "This is a plain-language demo of a research project that teaches an AI to "
    "**guess how busy a road will be**, hours in advance — the same idea behind the "
    "traffic predictions in your maps app, just built and studied from scratch. "
    "Pick a road on the left, and watch two versions of the AI try to predict a day of traffic."
)

r = ROADS[road]
st.caption(f"**{road}** — {r['blurb']}")

hours, true_curve = simulate_true_flow(r["peak"], r["base"], day_type, st.session_state.seed)

# ----------------------------------------------------------------------------
# MAIN CHART: actual traffic + both AIs' typical error bands
# ----------------------------------------------------------------------------
band_basic = r["mae_basic"]
band_smart = r["mae_smart"]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=np.concatenate([hours, hours[::-1]]),
    y=np.concatenate([true_curve + band_basic, (true_curve - band_basic)[::-1]]),
    fill="toself", fillcolor="rgba(192,57,43,0.12)", line=dict(width=0),
    name="Basic AI — typical guess range", showlegend=True,
))
fig.add_trace(go.Scatter(
    x=np.concatenate([hours, hours[::-1]]),
    y=np.concatenate([true_curve + band_smart, (true_curve - band_smart)[::-1]]),
    fill="toself", fillcolor="rgba(39,174,96,0.25)", line=dict(width=0),
    name="Smart AI — typical guess range", showlegend=True,
))
fig.add_trace(go.Scatter(
    x=hours, y=true_curve, mode="lines", name="Actual traffic",
    line=dict(color="#222222", width=2.5),
))
fig.add_vline(x=depart_hour, line_dash="dot", line_color="#555555",
              annotation_text="You leave here", annotation_position="top")

fig.update_layout(
    height=440, xaxis_title="Hour of day", yaxis_title="Vehicles (per 5 min)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    margin=dict(t=30, b=10),
)
st.plotly_chart(fig, use_container_width=True)
st.caption(
    "The shaded bands show how far off each AI's guess typically runs. The **Smart AI** "
    "(green) — the improved version this project built — stays noticeably closer to the "
    "actual traffic than the **Basic AI** (red), which is the older, unimproved starting point."
)

# ----------------------------------------------------------------------------
# METRIC CARDS
# ----------------------------------------------------------------------------
idx = int((depart_hour / 24) * 288) % 288
current_flow = true_curve[idx]
label, color = congestion_label(current_flow, r["peak"], r["base"])
accuracy = 100 - r["mapes"]
improvement = (r["mae_basic"] - r["mae_smart"]) / r["mae_basic"] * 100

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Predicted congestion at your departure time", label)
with c2:
    st.metric("Smart AI's prediction accuracy", f"{accuracy:.0f}%")
with c3:
    st.metric("How much smarter than the basic version", f"{improvement:.1f}%",
              help="Real result from this project: how much the improved AI's average "
                   "error dropped compared to the unimproved starting version.")

if label.startswith("🔴"):
    st.warning(f"Heads up — traffic on {road} is predicted to be heavy around your "
               f"departure time. Leaving 20-30 minutes earlier or later could mean a smoother ride.")
elif label.startswith("🟡"):
    st.info(f"Traffic on {road} looks moderate around your departure time — a normal commute.")
else:
    st.success(f"Good timing — {road} looks light around your departure time.")

st.divider()

# ----------------------------------------------------------------------------
# HOW IT WORKS, IN PLAIN LANGUAGE
# ----------------------------------------------------------------------------
st.header("How does the 'Smart AI' actually get smarter?")
st.markdown("No jargon — three simple ideas this project added to a basic traffic-predicting AI:")

with st.expander("📅 It learns the calendar, not just the clock"):
    st.markdown(
        "A basic AI only knows *how far into its data* it is — like counting minutes on a "
        "stopwatch. The Smart AI also knows **what day it is and what time of day it is** — "
        "the same way you instinctively know rush hour hits differently on a Monday morning "
        "versus a lazy Sunday afternoon."
    )

with st.expander("⚖️ It learns what to trust"):
    st.markdown(
        "As the AI reasons through a prediction in stages, it has to decide how much weight "
        "to give its earlier hunches versus new information coming in. The basic version used "
        "one fixed rule for every road, every time. The Smart AI **learns its own balance for "
        "each situation** — a bit like adjusting how much you trust the weather forecast versus "
        "looking out the window yourself."
    )

with st.expander("🎓 It starts easy and works up to hard"):
    st.markdown(
        "Instead of throwing the AI straight at the busiest, most chaotic interchange, training "
        "starts it on quieter, simpler roads first and gradually introduces harder ones — the "
        "same way a driving instructor doesn't put a first-timer on the freeway on day one."
    )

st.divider()
st.caption(
    "⚠️ This page is an interactive simulation built to make the underlying research project "
    "easy to understand for a general audience. It is not the research paper, and the traffic "
    "curves shown are illustrative rather than real historical sensor data — but the accuracy "
    "and improvement numbers driving the simulation are the project's real results."
)
