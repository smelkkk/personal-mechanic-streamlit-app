import streamlit as st

st.set_page_config(page_title="Personal Mechanic", layout="wide")


def init_state():
    if "case" not in st.session_state:
        st.session_state.case = {
            "driving_now": False,
            "mileage": 80000,
            "car_model": "Generic",
            "warning_type": "Check engine",
            "light_behavior": "Steady",
            "after_refuel": False,
            "symptoms": [],
        }
    if "decision" not in st.session_state:
        st.session_state.decision = None
    if "report" not in st.session_state:
        st.session_state.report = None


def sidebar_inputs():
    st.sidebar.header("Context")

    st.session_state.case["car_model"] = st.sidebar.selectbox(
        "Car model",
        ["Generic", "Toyota", "BMW", "Mercedes", "Audi", "Volkswagen", "Tesla (EV)"],
        index=0,
    )
    st.session_state.case["mileage"] = st.sidebar.number_input(
        "Mileage (km)", min_value=0, max_value=500000, value=st.session_state.case["mileage"], step=1000
    )
    st.session_state.case["driving_now"] = st.sidebar.toggle(
        "I’m currently driving", value=st.session_state.case["driving_now"]
    )

    st.sidebar.divider()
    st.sidebar.header("Demo controls")

    st.session_state.case["warning_type"] = st.sidebar.selectbox(
        "Warning type (demo)",
        ["Check engine", "Oil pressure", "Battery/charging", "Engine temperature", "Brake warning"],
        index=0,
    )


def main():
    init_state()
    sidebar_inputs()

    st.title("Personal Mechanic")
    st.caption("Prototype: AI-assisted triage + mechanic report")

    tab_diag, tab_rec, tab_rep, tab_about = st.tabs(
        ["Diagnose", "Recommendation", "Mechanic Report", "About"]
    )

    with tab_diag:
        st.subheader("Diagnose")
        st.write("Answer a few questions so I can guide you safely.")

        col1, col2 = st.columns(2)

        with col1:
            st.session_state.case["light_behavior"] = st.radio(
                "Is the warning light steady or flashing?",
                ["Steady", "Flashing"],
                index=0 if st.session_state.case["light_behavior"] == "Steady" else 1,
            )
            st.session_state.case["after_refuel"] = st.toggle(
                "Did it appear right after refueling?",
                value=st.session_state.case["after_refuel"],
            )

        with col2:
            st.session_state.case["symptoms"] = st.multiselect(
                "Do you notice any of these right now?",
                ["Loss of power", "Shaking", "Burning smell", "Loud unusual noise", "Steam"],
                default=st.session_state.case["symptoms"],
            )

        st.info("Next step: we’ll compute a recommendation and generate a report.")

    with tab_rec:
        st.subheader("Recommendation")
        if st.session_state.decision is None:
            st.warning("No recommendation yet. Go to the Diagnose tab first.")
        else:
            st.write(st.session_state.decision)

    with tab_rep:
        st.subheader("Mechanic Report")
        if st.session_state.report is None:
            st.warning("No report yet. Generate a recommendation first.")
        else:
            st.text(st.session_state.report)

    with tab_about:
        st.subheader("About this prototype")
        st.write(
            """
This is a product prototype focused on user experience + AI pipeline.
- Inputs: warning type + light behavior + symptoms + context
- Decision: (next step) triage logic returns Drive OK / Service Soon / Stop Now
- Output: clear guidance + shareable mechanic report

Limitations: This is not a certified diagnostic tool.
"""
        )


if __name__ == "__main__":
    main()