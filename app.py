"""Streamlit interface for the PokeringDumDum beginner preflop lab."""

from __future__ import annotations

import random

import pandas as pd
import streamlit as st

from pokeringdumdum.preflop import (
    DISPLAY_RANKS,
    POSITIONS,
    all_starting_hand_labels,
    break_even_fold_probability,
    call_decision,
    chart_matrix,
    open_range,
    raise_expected_value,
    simulate_preflop_equity,
    starting_hand_label,
)

st.set_page_config(page_title="PokeringDumDum", page_icon="🃏", layout="wide")
st.title("PokeringDumDum 🃏")
st.caption("Learn preflop ranges, equity, pot odds, and bet-size trade-offs.")
st.warning(
    "Educational tool only. The charts are simplified six-max defaults, not GTO "
    "solutions or advice for gambling real money."
)

chart_tab, equity_tab, math_tab, quiz_tab = st.tabs(
    ["Preflop chart", "Equity simulator", "Decision math", "Range quiz"]
)

with chart_tab:
    st.subheader("First-in opening chart")
    st.write(
        "Use this only when everyone before you has folded. If somebody has "
        "already raised, switch to the equity simulator and decision-math tab."
    )
    position = st.selectbox("Position", POSITIONS, index=2)
    style = st.select_slider("Range tolerance", ["tight", "balanced", "loose"])
    matrix = chart_matrix(position, style)
    frame = pd.DataFrame(matrix, index=DISPLAY_RANKS, columns=DISPLAY_RANKS)
    st.dataframe(frame, use_container_width=True, height=520)
    selected = open_range(position, style)
    st.metric("Hands opened", f"{len(selected)} / 169 classes")
    st.caption("s = suited, o = offsuit; pairs have no suffix.")

with equity_tab:
    st.subheader("Monte Carlo preflop equity")
    col_a, col_b = st.columns(2)
    first = col_a.text_input("First card", "As", help="Examples: As, Td, 7c")
    second = col_b.text_input("Second card", "Kh")
    opponents = st.slider("Number of opponents", 1, 5, 1)
    range_name = st.selectbox(
        "Opponent range",
        ["random", "UTG tight", "UTG balanced", "CO balanced", "BTN loose"],
    )
    trials = st.select_slider("Simulations", [1_000, 5_000, 10_000, 25_000])
    seed = st.number_input("Random seed", value=7, step=1)
    if st.button("Run simulation", type="primary"):
        try:
            labels = None
            if range_name != "random":
                range_position, range_style = range_name.split()
                labels = open_range(range_position, range_style)
            with st.spinner("Dealing simulated boards..."):
                result = simulate_preflop_equity(
                    (first, second),
                    trials=trials,
                    opponents=opponents,
                    opponent_labels=labels,
                    seed=int(seed),
                )
            st.success(f"{starting_hand_label(first, second)} simulation complete")
            c1, c2, c3 = st.columns(3)
            c1.metric("Equity", f"{result.equity:.1%}")
            c2.metric("Win rate", f"{result.win_rate:.1%}")
            c3.metric("Tie rate", f"{result.tie_rate:.1%}")
            st.write(
                f"Approximate 95% Monte Carlo interval: "
                f"**[{result.ci95_low:.1%}, {result.ci95_high:.1%}]**"
            )
        except ValueError as error:
            st.error(str(error))

with math_tab:
    st.subheader("Call, fold, and raise arithmetic")
    equity = st.slider("Estimated equity", 0.0, 1.0, 0.40, 0.01)
    pot = st.number_input("Pot before your action", min_value=0.0, value=100.0)
    call = st.number_input("Amount to call", min_value=0.0, value=30.0)
    tolerance = st.slider(
        "Extra equity safety margin",
        0.0,
        0.15,
        0.03,
        0.01,
        help="Adds caution for estimation error; it is not a universal rule.",
    )
    action, required = call_decision(equity, pot, call, tolerance)
    st.metric("Simplified call decision", action)
    st.write(f"Required equity including margin: **{required:.1%}**")

    st.divider()
    st.write("**Stylized raise scenario**")
    risk = st.number_input(
        "Additional chips risked by raising", min_value=1.0, value=75.0
    )
    fold_probability = st.slider(
        "Estimated opponent fold probability", 0.0, 1.0, 0.35, 0.01
    )
    raise_ev = raise_expected_value(pot, risk, equity, fold_probability)
    break_even = break_even_fold_probability(pot, risk, equity)
    st.metric("Raise EV", f"{raise_ev:.2f} chips")
    st.write(f"Break-even opponent fold probability: **{break_even:.1%}**")
    st.caption(
        "This one-street model assumes one opponent either folds or calls the same "
        "additional amount. It does not model reraises or later streets."
    )

with quiz_tab:
    st.subheader("Opening-range quiz")
    quiz_position = st.selectbox("Quiz position", POSITIONS[:-1], index=2, key="quiz")
    quiz_style = st.selectbox("Quiz style", ["tight", "balanced", "loose"])
    if "quiz_hand" not in st.session_state:
        st.session_state.quiz_hand = random.choice(all_starting_hand_labels())
    st.markdown(f"## {st.session_state.quiz_hand}")
    answer = st.radio("First in: what do you do?", ["OPEN", "FOLD"], horizontal=True)
    if st.button("Check answer"):
        correct = (
            "OPEN"
            if st.session_state.quiz_hand in open_range(quiz_position, quiz_style)
            else "FOLD"
        )
        if answer == correct:
            st.success("Correct.")
        else:
            st.error(f"This chart says {correct}.")
    if st.button("Next hand"):
        st.session_state.quiz_hand = random.choice(all_starting_hand_labels())
        st.rerun()
