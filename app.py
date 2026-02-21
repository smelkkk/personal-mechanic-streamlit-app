import streamlit as st
from logic.triage import triage
from logic.report import build_report

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

    # -------------------------
    # Tab: Diagnose
    # -------------------------
    with tab_diag:
        st.subheader("Diagnose")
        st.write("Answer a few questions so I can guide you safely.")

        photo_cam = st.camera_input("Take a photo of the dashboard warning light (optional)")

        photo_upload = st.file_uploader(
            "Or upload a photo from your phone (recommended on iOS)",
            type=["png", "jpg", "jpeg"],
        )

        photo = photo_cam if photo_cam is not None else photo_upload
        st.session_state.case["photo_attached"] = photo is not None
        
        with st.form("triage_form", clear_on_submit=False):
            st.session_state.case["light_behavior"] = st.radio(
                "Is the warning light steady or flashing?",
                ["Steady", "Flashing"],
                index=0 if st.session_state.case["light_behavior"] == "Steady" else 1,
            )

            st.session_state.case["symptoms"] = st.multiselect(
                "Do you notice any of these right now?",
                ["Loss of power", "Shaking", "Burning smell", "Loud unusual noise", "Steam"],
                default=st.session_state.case["symptoms"],
            )

            st.session_state.case["after_refuel"] = st.toggle(
                "Did it appear right after refueling?",
                value=st.session_state.case["after_refuel"],
            )

            submitted = st.form_submit_button("Generate recommendation", type="primary")

        if submitted:
            result = triage(st.session_state.case)

            st.session_state.decision = {
                "Urgency": result.urgency,
                "Confidence": f"{int(result.confidence * 100)}%",
                "Top reasons": result.reasons,
                "Next steps": result.next_steps,
            }

            st.session_state.report = build_report(st.session_state.case, result)
            st.toast("Recommendation and report generated.")

        st.caption("Mobile-first flow: answer → submit → view recommendation/report in other tabs.")

    # -------------------------
    # Tab: Recommendation
    # -------------------------
    with tab_rec:
        st.subheader("Recommendation")

        if st.session_state.decision is None:
            st.warning("No recommendation yet. Go to Diagnose and click 'Generate recommendation'.")
        else:
            st.metric("Urgency", st.session_state.decision["Urgency"])
            st.metric("Confidence", st.session_state.decision["Confidence"])

            st.write("**Top reasons**")
            for r in st.session_state.decision["Top reasons"]:
                st.write(f"- {r}")

            st.write("**Next steps**")
            for i, step in enumerate(st.session_state.decision["Next steps"], start=1):
                st.write(f"{i}. {step}")

    # -------------------------
    # Tab: Mechanic Report
    # -------------------------
    with tab_rep:
        st.subheader("Mechanic Report")

        if st.session_state.report is None:
            st.warning("No report yet. Generate a recommendation first.")
        else:
            st.text_area("Report", st.session_state.report, height=320)

            st.download_button(
                "Download report (.txt)",
                data=st.session_state.report,
                file_name="mechanic_report.txt",
                mime="text/plain",
            )

    # -------------------------
    # Tab: About
    # -------------------------
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