import streamlit as st
from logic.triage import triage
from logic.report import build_report
from logic.llm import generate_text
from logic.mechanic_finder import find_mechanics

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
    if "mechanic_result" not in st.session_state:
        st.session_state.mechanic_result = None


def sidebar_inputs():
    st.sidebar.header("Context")

    st.sidebar.divider()
    st.sidebar.header("AI")
    st.session_state.case["ai_mode"] = st.sidebar.toggle("AI explanations (LLM)", value=False)

    st.session_state.case["car_model"] = st.sidebar.selectbox(
        "Car model",
        ["Generic", "Toyota", "BMW", "Mercedes", "Audi", "Volkswagen", "Tesla (EV)"],
        index=0,
    )
    st.session_state.case["mileage"] = st.sidebar.number_input(
        "Mileage (km)", min_value=0, max_value=500000,
        value=st.session_state.case["mileage"], step=1000
    )
    st.session_state.case["driving_now"] = st.sidebar.toggle(
        "I'm currently driving", value=st.session_state.case["driving_now"]
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
    st.caption("Prototype: AI-assisted triage + mechanic report + mechanic finder")

    tab_diag, tab_rec, tab_rep, tab_find, tab_about = st.tabs(
        ["Diagnose", "Recommendation", "Mechanic Report", "Find a Mechanic", "About"]
    )

    # -------------------------
    # Tab: Diagnose
    # -------------------------
    with tab_diag:
        st.subheader("Diagnose")
        st.write("Answer a few questions so I can guide you safely.")

        photo = st.file_uploader(
            "Upload a photo of the dashboard warning light (optional)",
            type=["png", "jpg", "jpeg"],
        )
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

            # Reset mechanic result whenever a new triage is run
            st.session_state.mechanic_result = None

            base_report = build_report(st.session_state.case, result)

            if st.session_state.case.get("ai_mode"):
                with st.spinner("Generating explanation and report..."):
                    ok, out, err = generate_text(
                        st.session_state.case,
                        st.session_state.decision,
                        base_report
                    )

                if ok:
                    st.session_state.case["ai_explanation"] = out["explanation"]
                    st.session_state.report = out["report"]
                else:
                    st.session_state.case["ai_explanation"] = None
                    st.session_state.report = base_report
                    st.warning(err)
            else:
                st.session_state.case["ai_explanation"] = None
                st.session_state.report = base_report

            st.toast("Recommendation and report generated.")
            st.success("Recommendation generated.")

            urgency = st.session_state.decision["Urgency"]
            confidence = st.session_state.decision["Confidence"]

            if urgency == "Stop Now":
                st.error(f"🛑 **{urgency}** — Confidence: {confidence}")
            elif urgency == "Service Soon":
                st.warning(f"🟠 **{urgency}** — Confidence: {confidence}")
            else:
                st.success(f"🟢 **{urgency}** — Confidence: {confidence}")

            st.caption("Open the **Recommendation** tab for full details, or **Find a Mechanic** to locate nearby workshops.")

    # -------------------------
    # Tab: Recommendation
    # -------------------------
    with tab_rec:
        st.subheader("Recommendation")

        if st.session_state.decision is None:
            st.warning("No recommendation yet. Go to Diagnose and click 'Generate recommendation'.")
        else:
            urgency = st.session_state.decision["Urgency"]
            confidence = st.session_state.decision["Confidence"]

            if urgency == "Stop Now":
                st.error(f"🛑 **{urgency}** — Safety first.")
            elif urgency == "Service Soon":
                st.warning(f"🟠 **{urgency}** — Needs attention soon.")
            else:
                st.success(f"🟢 **{urgency}** — Monitor and continue carefully.")

            c1, c2 = st.columns(2)
            c1.metric("Urgency", urgency)
            c2.metric("Confidence", confidence)

            with st.expander("Top reasons", expanded=True):
                for r in st.session_state.decision["Top reasons"]:
                    st.write(f"• {r}")

            with st.expander("Next steps", expanded=True):
                for i, step in enumerate(st.session_state.decision["Next steps"], start=1):
                    st.write(f"{i}. {step}")

            exp = st.session_state.case.get("ai_explanation")
            if exp:
                st.markdown("---")
                st.write("### AI explanation")
                st.info(exp)

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
    # Tab: Find a Mechanic
    # -------------------------
    with tab_find:
        st.subheader("Find a Mechanic Nearby")

        if st.session_state.decision is None:
            st.info("Generate a recommendation first (Diagnose tab), then come back here to find nearby mechanics.")
        else:
            urgency = st.session_state.decision["Urgency"]

            if urgency == "Stop Now":
                st.error("🛑 Your situation is urgent. Find a mechanic or call roadside assistance now.")
            elif urgency == "Service Soon":
                st.warning("🟠 You should visit a mechanic within 24–48 hours.")
            else:
                st.success("🟢 No rush — schedule a check when convenient.")

            st.markdown("---")
            st.write("Enter your current location to find nearby repair shops via OpenStreetMap (free, no account needed).")

            with st.form("location_form"):
                col1, col2 = st.columns(2)
                with col1:
                    lat = st.number_input(
                        "Latitude", value=40.4168, format="%.4f",
                        help="e.g. 40.4168 for Madrid, 48.8566 for Paris"
                    )
                with col2:
                    lon = st.number_input(
                        "Longitude", value=-3.7038, format="%.4f",
                        help="e.g. -3.7038 for Madrid, 2.3522 for Paris"
                    )

                if not st.session_state.case.get("ai_mode"):
                    st.caption(
                        "💡 **Tip:** Enable **AI explanations** in the sidebar to get an AI-powered "
                        "ranking and recommendation for the shops found."
                    )

                find_submitted = st.form_submit_button("🔍 Find mechanics", type="primary")

            if find_submitted:
                with st.spinner("Searching OpenStreetMap for nearby repair shops…"):
                    ai_mode = st.session_state.case.get("ai_mode", False)

                    if ai_mode:
                        ok, result, err = find_mechanics(
                            lat=lat,
                            lon=lon,
                            urgency=urgency,
                            warning_type=st.session_state.case.get("warning_type", ""),
                            symptoms=st.session_state.case.get("symptoms", []),
                        )
                        if not ok:
                            st.warning(f"AI search failed: {err}. Falling back to direct search.")
                            ai_mode = False

                    if not ai_mode:
                        # Fallback: direct Overpass query without LLM
                        from logic.mechanic_finder import _query_overpass
                        radius = {"Stop Now": 2000, "Service Soon": 5000, "Drive OK": 10000}.get(urgency, 5000)
                        mechanics = _query_overpass(lat, lon, radius)
                        result = {
                            "mechanics": mechanics,
                            "summary": None,
                            "rationale": f"Searched within {radius // 1000} km based on urgency level.",
                            "radius_km": radius // 1000,
                            "open_now_priority": urgency == "Stop Now",
                        }
                        ok = True

                    st.session_state.mechanic_result = result

            # Display results
            if st.session_state.mechanic_result:
                result = st.session_state.mechanic_result
                mechanics = result.get("mechanics", [])

                st.markdown(f"**Search radius:** {result.get('radius_km', '?')} km  |  "
                            f"**Shops found:** {len(mechanics)}")

                if result.get("rationale"):
                    st.caption(f"🤖 AI search reasoning: *{result['rationale']}*")

                if result.get("summary"):
                    st.info(f"**AI recommendation:** {result['summary']}")

                if not mechanics:
                    st.warning(
                        "No repair shops found in OpenStreetMap for this area. "
                        "Try a different location or search manually on maps.openstreetmap.org"
                    )
                else:
                    st.markdown("### Nearby repair shops")
                    for i, m in enumerate(mechanics, start=1):
                        with st.expander(
                            f"{'🛑 ' if i == 1 and urgency == 'Stop Now' else ''}"
                            f"{i}. {m['name']} — {m['distance_km']} km away",
                            expanded=(i == 1),
                        ):
                            cols = st.columns(2)
                            with cols[0]:
                                if m["address"]:
                                    st.write(f"📍 **Address:** {m['address']}")
                                if m["phone"]:
                                    st.write(f"📞 **Phone:** {m['phone']}")
                            with cols[1]:
                                if m["opening_hours"]:
                                    st.write(f"🕐 **Hours:** {m['opening_hours']}")
                                osm_url = f"https://www.openstreetmap.org/?mlat={m['lat']}&mlon={m['lon']}#map=16/{m['lat']}/{m['lon']}"
                                st.markdown(f"[📌 View on OpenStreetMap]({osm_url})")

                    # Static map via OpenStreetMap embed (first result)
                    if mechanics:
                        first = mechanics[0]
                        map_url = (
                            f"https://www.openstreetmap.org/export/embed.html"
                            f"?bbox={first['lon']-0.03},{first['lat']-0.02},{first['lon']+0.03},{first['lat']+0.02}"
                            f"&layer=mapnik&marker={first['lat']},{first['lon']}"
                        )
                        st.markdown("### Map (closest shop)")
                        st.components.v1.iframe(map_url, height=300)

    # -------------------------
    # Tab: About
    # -------------------------
    with tab_about:
        st.subheader("About this prototype")
        st.write(
            """
This is a product prototype focused on user experience + AI pipeline.

**Assignment 1 features:**
- Inputs: warning type + light behavior + symptoms + context
- Rule-based triage: Drive OK / Service Soon / Stop Now
- LLM (OpenAI): plain-language explanation + formatted mechanic report

**Assignment 2 additions:**
- **Mechanic Finder** using LLM tool use + OpenStreetMap (Overpass API)
  - LLM Call 1: decides search radius and urgency flags via a tool call
  - Overpass API: fetches real nearby repair shops (free, no API key needed)
  - LLM Call 2: ranks and summarises results for the driver
- Works without AI mode too (direct Overpass search, urgency-based radius)

**Limitations:** Not a certified diagnostic tool. OSM data may be incomplete in some areas.
"""
        )


if __name__ == "__main__":
    main()