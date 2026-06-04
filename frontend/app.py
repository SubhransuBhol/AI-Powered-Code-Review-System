import streamlit as st
import requests

st.set_page_config(
    page_title="AI Code Reviewer",
    layout="wide"
)

with st.sidebar:

    st.title("🤖 AI Code Reviewer")

    st.markdown("---")

    st.markdown("""
    ### Features

    - ZIP Project Review

    - GitHub Repository Review

    - Hybrid Retrieval

    - AI-Powered Security Analysis

    - Markdown Report Download
    """)

    st.markdown("---")

    st.caption(
        "Powered by RAG + Ollama"
    )
st.title("AI Code Reviewer")

st.caption(
    "Repository Security & Quality Analysis"
)

st.markdown("---")

tab1, tab2 = st.tabs(
    [
        "📦 ZIP Upload",
        "🔗 GitHub Repository"
    ]
)

# ZIP REVIEW SECTION


with tab1:

    st.header("Review ZIP Project")

    uploaded_file = st.file_uploader(
        "Upload ZIP File",
        type=["zip"]
    )

    if uploaded_file:

        st.success(
            f"Selected: {uploaded_file.name}"
        )

        if st.button("Review ZIP Project"):

            with st.spinner(
                "Analyzing project... This may take 2-3 minutes."
            ):

                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file,
                        "application/zip"
                    )
                }

                response = requests.post(
                    "http://127.0.0.1:8000/review-project",
                    files=files
                )

                if response.status_code == 200:

                    result = response.json()

                    st.success("Review completed successfully!")

                    st.info(f"Report generated: {result['report_file']}")

                    with st.expander(
                        "📄 View Report"
                    ):

                        st.markdown(
                            result["report"]
                        )

                    download_url = (
                        f"http://127.0.0.1:8000/download-report/"
                        f"{result['report_file']}"
                    )

                    pdf_url = (
                        f"http://127.0.0.1:8000/download-pdf/"
                        f"{result['pdf_file']}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        st.link_button(
                            "⬇️ Download Markdown",
                            download_url
                        )

                    with col2:

                        st.link_button(
                            "📄 Download PDF",
                            pdf_url
                        )
                else:

                    st.error(
                        response.text
                    )


# GITHUB REVIEW SECTION

with tab2:

    st.header(
        "Review GitHub Repository"
    )

    repo_url = st.text_input(
        "GitHub Repository URL"
    )

    if st.button(
        "Review GitHub Repository"
    ):

        if repo_url:

            with st.spinner(
                "Cloning repository and reviewing...This may take 2-3 minutes."
            ):

                response = requests.post(
                    "http://127.0.0.1:8000/review-github",
                    json={
                        "repo_url": repo_url
                    }
                )

                if response.status_code == 200:

                    result = response.json()

                    st.success("Repository review completed successfully!")

                    st.info(f"Report generated: {result['report_file']}")

                    with st.expander(
                        "📄 View Report"
                    ):

                        st.markdown(
                            result["report"]
                        )

                    download_url = (
                        f"http://127.0.0.1:8000/download-report/"
                        f"{result['report_file']}"
                    )
                    
                    pdf_url = (
                        f"http://127.0.0.1:8000/download-pdf/"
                        f"{result['pdf_file']}"
                    )
                    
                    col1, col2 = st.columns(2)

                    with col1:

                        st.link_button(
                            "⬇️ Download Markdown",
                            download_url
                        )

                    with col2:

                        st.link_button(
                            "📄 Download PDF",
                            pdf_url
                        )

                else:

                    st.error(
                        response.text
                    )