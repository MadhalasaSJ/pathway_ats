import os
import io
import json
import html as _html
import streamlit as st

from utils.text_extract import extract_text_from_file
from utils.back4app_mcp import save_evaluation

# Try importing LLM analyzer
try:
    from utils.model_ats import analyze_resume, ACTIVE_PROVIDER, ACTIVE_MODEL
    ANALYSIS_READY = True
    ANALYSIS_ERROR = None
except Exception as e:
    ANALYSIS_READY = False
    ANALYSIS_ERROR = str(e)


st.set_page_config(page_title="AI ATS Checker", layout="wide")


def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def main():
    load_css()
    st.title("AI-powered ATS Checker")
    st.markdown(
        "Upload a resume (PDF or DOCX) and paste or upload a job description. Click Analyze to evaluate."
    )

    # Provider Info
    if ANALYSIS_READY:
        st.info(f"📡 Using {ACTIVE_PROVIDER} – Model: {ACTIVE_MODEL}")
    else:
        st.error(f"⚠️ Analysis not available: {ANALYSIS_ERROR}")
        st.stop()

    # -------------------------------------------------------------------
    # FIX: Entire UI wrapped inside one card container
    # -------------------------------------------------------------------
    with st.container():
        st.markdown('<div class="app-card">', unsafe_allow_html=True)

        # Add tiny spacing fix to prevent ghost block
        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns([1, 2])

        # ---------------- LEFT PANEL (INPUTS) ----------------
        with col1:
            st.header("Inputs")

            resume_file = st.file_uploader(
                "Upload resume (PDF or DOCX)", type=["pdf", "docx"]
            )

            jd_file = st.file_uploader(
                "Upload job description (optional, PDF/DOCX/TXT)",
                type=["pdf", "docx", "txt"]
            )

            jd_text_area = st.text_area(
                "Or paste job description (overrides uploaded file if present)",
                height=200
            )

            analyze_btn = st.button("Analyze")

        # ---------------- RIGHT PANEL (RESULTS) ----------------
        with col2:
            st.header("Results")
            results_container = st.empty()

        # --------------------- ANALYSIS FLOW ---------------------
        if analyze_btn:

            if not resume_file:
                st.error("Please upload a resume file.")
                st.markdown('</div>', unsafe_allow_html=True)
                return

            # Extract resume text
            try:
                resume_text = extract_text_from_file(resume_file)
            except Exception as e:
                st.error(f"Failed to extract resume text: {e}")
                st.markdown('</div>', unsafe_allow_html=True)
                return

            # JD extraction logic
            if jd_text_area.strip():
                job_text = jd_text_area
            elif jd_file:
                try:
                    job_text = extract_text_from_file(jd_file)
                except Exception as e:
                    st.warning(f"Failed to extract job description: {e}")
                    job_text = ""
            else:
                job_text = ""

            if not job_text.strip():
                st.warning("No job description provided — analysis only based on resume.")

            # Run AI
            with st.spinner("Analyzing with AI..."):
                try:
                    analysis = analyze_resume(resume_text, job_text)
                except Exception as e:
                    st.error(f"AI analysis failed: {e}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    return

            # Parse fields
            ats_score = analysis.get("ats_score")
            matched = analysis.get("matched_keywords", [])
            missing = analysis.get("missing_keywords", [])
            skill_gaps = analysis.get("skill_gaps", [])
            strengths = analysis.get("strengths", [])
            suggestions = analysis.get("suggestions", [])
            experience_relevance = analysis.get("experience_relevance")

            # ------------------- RENDER RESULTS ---------------------
            with results_container.container():
                st.subheader(f"ATS Match Score: {ats_score}/100")
                st.metric("Experience Relevance", f"{experience_relevance}%")

                # Chip renderer
                def render_chips(items, kind="matched"):
                    if not items:
                        return "<div class='chips'><span class='chip'>—</span></div>"
                    cls = "chip-matched" if kind == "matched" else "chip-missing"
                    chips = [
                        f"<span class='chip {cls}'>{_html.escape(str(it))}</span>"
                        for it in items
                    ]
                    return f"<div class='chips'>{''.join(chips)}</div>"

                st.markdown("**Matched Keywords:**")
                st.markdown(render_chips(matched, "matched"), unsafe_allow_html=True)

                st.markdown("**Missing Keywords:**")
                st.markdown(render_chips(missing, "missing"), unsafe_allow_html=True)

                st.markdown("**Skill Gaps:**")
                if skill_gaps:
                    for g in skill_gaps:
                        st.markdown(
                            f"<div class='list-item'><span class='strength'>•</span> {_html.escape(g)}</div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown("<div class='list-item'>—</div>", unsafe_allow_html=True)

                st.markdown("**Strengths:**")
                if strengths:
                    for s in strengths:
                        st.markdown(
                            f"<div class='list-item'><span class='strength'>✓</span> {_html.escape(s)}</div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown("<div class='list-item'>—</div>", unsafe_allow_html=True)

                st.markdown("**Improvement Suggestions:**")
                if suggestions:
                    for s in suggestions:
                        st.markdown(
                            f"<div class='list-item suggestion'>- {_html.escape(s)}</div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown("<div class='list-item'>—</div>", unsafe_allow_html=True)

                with st.expander("Raw JSON output"):
                    st.json(analysis)

            # ------------------- SAVE TO BACK4APP -------------------
            try:
                payload = {
                    "resume_text": resume_text[:30000],
                    "job_text": job_text[:30000],
                    "ats_score": ats_score,
                    "missing_keywords": missing,
                }
                res = save_evaluation(payload)
                if res.get("objectId"):
                    st.success("Evaluation saved to Back4App.")
                else:
                    st.warning("Evaluation not saved.")
            except Exception as e:
                st.warning(f"Could not save to Back4App: {e}")

        # Close the card
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
