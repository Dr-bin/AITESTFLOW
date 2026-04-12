"""Streamlit web application for AITestFlow - AI-Driven Black-Box Testing Platform"""

import json

import streamlit as st
import yaml

from src.coordinator import WorkflowCoordinator
from src.models import CoverageState


def parse_openapi_file(uploaded_file) -> dict:
    """Parse uploaded OpenAPI file (YAML or JSON)"""
    content = uploaded_file.getvalue().decode("utf-8")
    if uploaded_file.name.endswith(".json"):
        return json.loads(content)
    return yaml.safe_load(content)


def save_workflow_log(coordinator: WorkflowCoordinator) -> str:
    """Get workflow log content"""
    log = getattr(coordinator, "_workflow_log", [])
    return "".join(log) if log else ""


def main() -> None:
    """Main application entry point"""
    st.set_page_config(
        page_title="AITestFlow",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
        <style>
        .main-title {
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }
        .subtitle {
            font-size: 1.1rem !important;
            color: #6c757d !important;
            margin-bottom: 2rem !important;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%) !important;
            border-right: 1px solid #e9ecef !important;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #495057 !important;
        }
        .stButton > button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        .info-box {
            background: linear-gradient(135deg, #e8f4fd 0%, #f0f7ff 100%);
            border-left: 4px solid #667eea;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 700 !important;
        }
        [data-testid="stMetric"] {
            background: white;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<p class="main-title">🧪 AITestFlow - AI-Driven Black-Box Testing Platform</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p class="subtitle">智能化 API 测试用例自动生成平台 | 基于 OpenAPI 规范自动创建黑盒测试</p>',
        unsafe_allow_html=True
    )
    st.markdown("---")

    with st.sidebar:
        st.markdown(
            '<h3 style="margin-bottom: 1rem;">📁 Configuration</h3>',
            unsafe_allow_html=True
        )

        uploaded_file = st.file_uploader(
            "Upload OpenAPI Spec",
            type=["yaml", "yml", "json"],
            help="Upload OpenAPI YAML or JSON file",
        )

        st.markdown("---")

        st.markdown("### ⚙️ Generation Settings")

        coverage_threshold = st.slider(
            "Coverage Threshold",
            min_value=0.5,
            max_value=0.95,
            value=0.85,
            step=0.05,
            help="Target coverage rate (0.5-0.95)",
        )

        max_iterations = st.slider(
            "Max Iterations",
            min_value=1,
            max_value=5,
            value=3,
            step=1,
            help="Maximum feedback iterations per endpoint",
        )

    if "coordinator" not in st.session_state:
        st.session_state["coordinator"] = None
    if "results_ready" not in st.session_state:
        st.session_state["results_ready"] = False
    if "coverage_state" not in st.session_state:
        st.session_state["coverage_state"] = None

    main_col1, main_col2 = st.columns([3, 1])

    with main_col1:
        if uploaded_file:
            st.success(f"✅ File loaded: {uploaded_file.name}")
        else:
            st.info("📌 Waiting for file upload...")

    with main_col2:
        generate_clicked = st.button(
            "🚀 Generate Test Suite",
            type="primary",
            disabled=uploaded_file is None,
            use_container_width=True,
        )

    if generate_clicked and uploaded_file is not None:
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.markdown("📂 **Loading OpenAPI specification...**")
            progress_bar.progress(10)

            openapi_spec = parse_openapi_file(uploaded_file)

            status_text.markdown("⚙️ **Initializing WorkflowCoordinator...**")
            progress_bar.progress(20)

            coordinator = WorkflowCoordinator(
                coverage_threshold=coverage_threshold,
                max_iter=max_iterations,
                output_dir="output",
            )
            st.session_state["coordinator"] = coordinator

            status_text.markdown("🔄 **Running test generation pipeline...**")
            progress_bar.progress(30)

            test_code, coverage_state = coordinator.run_full_pipeline(openapi_spec)

            progress_bar.progress(90)
            status_text.markdown("✅ **Pipeline complete!**")
            progress_bar.progress(100)

            st.session_state["coverage_state"] = coverage_state
            st.session_state["test_code"] = test_code
            st.session_state["results_ready"] = True

            workflow_log = save_workflow_log(coordinator)
            st.session_state["workflow_log"] = workflow_log if workflow_log else "No workflow log available."

        except Exception as e:
            st.error(f"❌ Error during pipeline execution: {str(e)}")
            progress_bar.progress(0)
            status_text.text("")

    if st.session_state.get("results_ready"):
        st.markdown("---")

        with st.expander("📜 Workflow Decision Log", expanded=False):
            st.text(st.session_state.get("workflow_log", ""))

        st.markdown("### 📥 Download Generated Artifacts")

        test_code = st.session_state.get("test_code", "")
        workflow_log = st.session_state.get("workflow_log", "")
        coverage_state = st.session_state.get("coverage_state")

        col_d1, col_d2, col_d3 = st.columns(3)

        with col_d1:
            st.download_button(
                label="📄 Download test_api.py",
                data=test_code,
                file_name="test_api.py",
                mime="text/x-python",
                use_container_width=True,
            )

        if coverage_state:
            coverage_report = {
                "timestamp": coverage_state.model_dump().get("timestamp", ""),
                "total_conditions": coverage_state.total_conditions,
                "covered_condition_ids": coverage_state.covered_condition_ids,
                "coverage_rate": coverage_state.coverage_rate,
                "failed_test_cases": coverage_state.failed_test_cases,
                "iteration": coverage_state.iteration,
            }

            with col_d2:
                st.download_button(
                    label="📊 Download coverage_report.json",
                    data=json.dumps(coverage_report, indent=2),
                    file_name="coverage_report.json",
                    mime="application/json",
                    use_container_width=True,
                )

        with col_d3:
            st.download_button(
                label="📋 Download workflow_log.txt",
                data=workflow_log,
                file_name="workflow_log.txt",
                mime="text/plain",
                use_container_width=True,
            )

        st.markdown("---")

        if coverage_state:
            st.markdown("### 📈 Coverage Metrics")

            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric(label="Coverage Rate", value=f"{coverage_state.coverage_rate:.1%}")
            with m2:
                st.metric(label="Total Conditions", value=coverage_state.total_conditions)
            with m3:
                st.metric(label="Iterations", value=coverage_state.iteration)

        st.markdown("---")

        st.markdown(
            """
            <div class="info-box">
                <h4>⚠️ AI Limitations & Considerations</h4>
                <ul>
                    <li>AI-generated tests may not cover all edge cases</li>
                    <li>LLM outputs are non-deterministic; results may vary</li>
                    <li>Coverage metrics are estimates based on condition tracking</li>
                    <li>Generated tests require human review before production use</li>
                    <li>Feedback loop quality depends on LLM response accuracy</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()