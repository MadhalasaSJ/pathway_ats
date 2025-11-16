import os
import io
import json
import html as _html
import streamlit as st

from utils.text_extract import extract_text_from_file
from utils.back4app_mcp import save_evaluation

# Try to import the analysis module, catch initialization errors
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

    st.markdown("Upload a resume (PDF or DOCX) and paste or upload a job description. Click Analyze to evaluate.")
    
    # Show which provider is active
    if ANALYSIS_READY:
        st.info(f"📡 Using {ACTIVE_PROVIDER} – Model: {ACTIVE_MODEL}")
    else:
        st.error(f"⚠️ Analysis not available: {ANALYSIS_ERROR}")
        st.stop()

    # Wrap main content in an app-card so the page background is visible
    st.markdown('<div class="app-card">', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Inputs")
        resume_file = st.file_uploader("Upload resume (PDF or DOCX)", type=["pdf", "docx"])    
        jd_file = st.file_uploader("Upload job description (optional, PDF/DOCX/TXT)", type=["pdf","docx","txt"])    
        jd_text_area = st.text_area("Or paste job description (overrides uploaded file if present)", height=200)

        analyze_btn = st.button("Analyze")

    with col2:
        st.header("Results")
        results_container = st.empty()

    if analyze_btn:
        if not resume_file:
            st.error("Please upload a resume file.")
            return

        # Extract resume text
        try:
            resume_text = extract_text_from_file(resume_file)
        except Exception as e:
            st.error(f"Failed to extract resume text: {e}")
            return

        # Get job description text
        job_text = ""
        if jd_text_area and jd_text_area.strip():
            job_text = jd_text_area
        elif jd_file:
            try:
                job_text = extract_text_from_file(jd_file)
            except Exception as e:
                st.warning(f"Failed to extract job description file: {e}")

        if not job_text or not job_text.strip():
            st.warning("No job description provided — results will be based only on resume analysis.")

        with st.spinner("Analyzing with OpenAI..."):
            try:
                analysis = analyze_resume(resume_text, job_text)
            except Exception as e:
                st.error(f"OpenAI analysis failed: {e}")
                return

        # Display results
        try:
            ats_score = analysis.get("ats_score")
            matched = analysis.get("matched_keywords", [])
            missing = analysis.get("missing_keywords", [])
            skill_gaps = analysis.get("skill_gaps", [])
            strengths = analysis.get("strengths", [])
            suggestions = analysis.get("suggestions", [])
            experience_relevance = analysis.get("experience_relevance")
        except Exception:
            st.error("Unexpected analysis format from OpenAI.")
            st.json(analysis)
            return

        with results_container.container():
            st.subheader(f"ATS Match Score: {ats_score}/100")
            st.metric("Experience Relevance", f"{experience_relevance}%")

            # Render matched keywords as chips
            st.markdown("**Matched Keywords:**")
            def render_chips(items, kind="matched"):
                if not items:
                    return "<div class='chips'><span class='chip'>—</span></div>"
                chips = []
                cls = "chip-matched" if kind == "matched" else "chip-missing"
                for it in items:
                    esc = _html.escape(str(it))
                    chips.append(f"<span class='chip {cls}'>{esc}</span>")
                return f"<div class='chips'>{''.join(chips)}</div>"

            st.markdown(render_chips(matched, "matched"), unsafe_allow_html=True)

            st.markdown("**Missing Keywords:**")
            st.markdown(render_chips(missing, "missing"), unsafe_allow_html=True)

            st.markdown("**Skill Gaps:**")
            if skill_gaps:
                for g in skill_gaps:
                    st.markdown(f"<div class='list-item'><span class='strength'>•</span> {_html.escape(g)}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='list-item'>—</div>", unsafe_allow_html=True)

            st.markdown("**Strengths:**")
            if strengths:
                for s in strengths:
                    st.markdown(f"<div class='list-item'><span class='strength'>✓</span> {_html.escape(s)}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='list-item'>—</div>", unsafe_allow_html=True)

            st.markdown("**Improvement Suggestions:**")
            if suggestions:
                for s in suggestions:
                    st.markdown(f"<div class='list-item suggestion'>- {_html.escape(s)}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='list-item'>—</div>", unsafe_allow_html=True)

            # Raw JSON viewer
            with st.expander("Raw JSON output"):
                st.json(analysis)

        # Save to Back4App
        try:
            save_payload = {
                "resume_text": resume_text[:30000],
                "job_text": job_text[:30000],
                "ats_score": ats_score,
                "missing_keywords": missing,
            }
            save_res = save_evaluation(save_payload)
            if save_res.get("objectId"):
                st.success("Evaluation saved to Back4App.")
            else:
                st.warning("Evaluation not saved: unexpected response from Back4App.")
        except Exception as e:
            st.warning(f"Could not save to Back4App: {e}")

        # close the app-card wrapper
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
