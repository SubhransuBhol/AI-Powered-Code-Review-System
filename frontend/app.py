import streamlit as st
import requests

st.set_page_config(
    page_title="AI Code Reviewer",
    layout="wide"
)

# Session state initialization
if "open_ai_assistant" not in st.session_state:
    st.session_state["open_ai_assistant"] = False

if "is_generating" not in st.session_state:
    st.session_state["is_generating"] = False


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
            # Clear previous chat cache and history
            try:
                requests.post("http://127.0.0.1:8000/clear-chat")
            except Exception:
                pass
            st.session_state["zip_chat_history"] = []
            st.session_state["zip_button_answer"] = None
            st.session_state["zip_button_question"] = None
            st.session_state["github_chat_history"] = []
            st.session_state["github_button_answer"] = None
            st.session_state["github_button_question"] = None
            st.session_state["chat_history"] = []
            st.session_state["chat_cache"] = {}
            st.session_state["current_report_hash"] = None
            st.session_state["review_context"] = None
            st.session_state["open_ai_assistant"] = False
            st.session_state.pop("review_result", None)
            st.session_state.pop("report", None)

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
                    st.session_state["review_result"] = result
                    st.session_state["report"] = result["report"]
                    st.session_state["open_ai_assistant"] = True
                    st.session_state["review_context"] = result.get("review_context")
                    st.session_state["tab"] = "zip"
                    st.session_state["zip_chat_history"] = []
                    st.session_state["zip_button_answer"] = None
                    st.session_state["zip_button_question"] = None
                    st.session_state["github_chat_history"] = []
                    st.session_state["github_button_answer"] = None
                    st.session_state["github_button_question"] = None
                    st.session_state["chat_history"] = []
                    st.session_state["chat_cache"] = {}
                    st.session_state["current_report_hash"] = None
                    st.success("Review completed successfully!")
                else:
                    st.error(response.text)

        # Render report if it is in session state for zip tab
        if st.session_state.get("review_result") and st.session_state.get("tab") == "zip":
            result = st.session_state["review_result"]
            st.info(f"Report generated: {result['report_file']}")

            with st.expander("📄 View Report"):
                st.markdown(result["report"])

            download_url = f"http://127.0.0.1:8000/download-report/{result['report_file']}"
            pdf_url = f"http://127.0.0.1:8000/download-pdf/{result['pdf_file']}"

            st.markdown("")

            space1, btn1, gap, btn2, space2 = st.columns(
                [1, 2, 0.5, 2, 1]
            )

            with btn1:
                st.link_button(
                    "⬇️ Download Markdown",
                    download_url,
                    use_container_width=True
                )

            with btn2:
                st.link_button(
                    "📄 Download PDF",
                    pdf_url,
                    use_container_width=True
                )
                
            # Chat expander
            st.markdown("---")
            if "zip_chat_history" not in st.session_state:
                st.session_state["zip_chat_history"] = []
            if "zip_button_answer" not in st.session_state:
                st.session_state["zip_button_answer"] = None
            if "zip_button_question" not in st.session_state:
                st.session_state["zip_button_question"] = None

            with st.expander(" AI Review Assistant",
                expanded=st.session_state.get(
                    "open_ai_assistant",
                    False
                )
            ):
                st.write("###  AI Review Assistant")
                st.markdown("---")
                
                # Render conversation history (if active)
                if st.session_state["zip_chat_history"]:
                    st.markdown("#### Custom Q&A Chat")
                    for msg in st.session_state["zip_chat_history"]:
                        if msg["role"] == "user":
                            st.write(f" **You:** {msg['content']}")
                        else:
                            st.info(f" **Assistant:** {msg['content']}")
                    st.markdown("---")
                
                # Render single button response (if active)
                if st.session_state["zip_button_answer"]:
                    st.markdown(f"**Quick Section Guide:** **{st.session_state['zip_button_question']}**")
                    st.info(st.session_state["zip_button_answer"])
                    st.markdown("---")
                
                # Predefined question buttons
                col_c1, col_c2, col_c3 = st.columns(3)
                col_c4, col_c5, col_c6 = st.columns(3)
                
                predefined_question = None
                display_question = None
                
                with col_c1:
                    if st.button("🔍 Explain Critical Issues", key="zip_btn1"):
                        predefined_question = "Explain the critical issues found in this review. For each issue explain:\n- why it occurs\n- possible impact\n- risk severity\n- recommended fix\n\nUse only findings present in the review.\nMaximum 150 words."
                        display_question = "Explain Critical Issues"
                with col_c2:
                    if st.button("⚠️ What Should I Fix First?", key="zip_btn2"):
                        predefined_question = "Based only on the review findings, prioritize all issues from highest risk to lowest risk.\n\nExplain:\n- what should be fixed first\n- why it is highest priority\n- recommended order of implementation\n\nMaximum 150 words."
                        display_question = "What Should I Fix First?"
                with col_c3:
                    if st.button("🛡️ Explain Security Risks", key="zip_btn3"):
                        predefined_question = "Explain only the security findings identified in the review.\n\nInclude:\n- security risk\n- attack impact\n- business impact\n- recommended remediation\n\nUse only findings present in the review.\n\nMaximum 150 words."
                        display_question = "Explain Security Risks"
                with col_c4:
                    if st.button("📋 Summarize Report", key="zip_btn4"):
                        predefined_question = "Provide a concise executive summary of the review.\n\nInclude:\n- overall project health\n- major findings\n- release readiness\n\nMaximum 150 words."
                        display_question = "Summarize Report"
                with col_c5:
                    if st.button("🏗️ Explain Architecture Analysis", key="zip_btn5"):
                        predefined_question = "Explain the architecture analysis section.\n\nInclude:\n- detected project structure\n- architecture observations\n- actual risks identified\n\nIf no architecture risks exist, explain why the architecture appears acceptable.\n\nMaximum 150 words."
                        display_question = "Explain Architecture Analysis"
                with col_c6:
                    if st.button("📦 Explain Dependency Security Analysis", key="zip_btn6"):
                        predefined_question = "Explain the dependency security analysis findings.\n\nIf vulnerable dependencies exist:\n- explain risks\n- explain impact\n- recommend upgrades\n\nIf no vulnerable dependencies exist:\n- explain that dependency health appears acceptable\n\nMaximum 150 words."
                        display_question = "Explain Dependency Security Analysis"
                
                
                with st.form("zip_chat_form", clear_on_submit=False):
                    # Custom input
                    custom_question = st.text_input(
                        "Ask a question about this review...",
                        placeholder="Ask a question about this review...",
                        key="zip_custom_input"
                    )
                
                    # Ask button
                    ask_clicked = st.form_submit_button("Ask")

                question_to_submit = None
                
                if predefined_question:
                    question_to_submit = predefined_question
                elif ask_clicked and custom_question:
                    display_question = custom_question
                    question_to_submit = custom_question
                    
                if question_to_submit:
                    with st.spinner("Thinking..."):
                        try:
                            if predefined_question:
                                def stream_zip_button():
                                    resp = requests.post(
                                        "http://127.0.0.1:8000/ask-review-stream",
                                        json={
                                            "report": result["report"],
                                            "question": question_to_submit,
                                            "history": [],
                                            "review_context": st.session_state.get("review_context")
                                        },
                                        stream=True
                                    )
                                    for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                                        if chunk:
                                            yield chunk
                                            
                                answer = st.write_stream(stream_zip_button())
                                st.session_state["zip_button_answer"] = answer
                                st.session_state["zip_button_question"] = display_question
                                st.session_state["open_ai_assistant"] = True
                                st.rerun()
                            elif ask_clicked and custom_question:
                                history_payload = st.session_state["zip_chat_history"][-5:]
                                def stream_zip_custom():
                                    resp = requests.post(
                                        "http://127.0.0.1:8000/ask-review-stream",
                                        json={
                                            "report": result["report"],
                                            "question": question_to_submit,
                                            "history": history_payload,
                                            "review_context": st.session_state.get("review_context")
                                        },
                                        stream=True
                                    )
                                    for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                                        if chunk:
                                            yield chunk
                                            
                                answer = st.write_stream(stream_zip_custom())
                                st.session_state["zip_button_answer"] = None # Custom clears button answer
                                st.session_state["zip_button_question"] = None
                                st.session_state["zip_chat_history"].append({"role": "user", "content": display_question})
                                st.session_state["zip_chat_history"].append({"role": "assistant", "content": answer})
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to connect to backend: {e}")


# GITHUB REVIEW SECTION
with tab2:
    st.header("Review GitHub Repository")
    repo_url = st.text_input(
        "GitHub Repository URL"
    )

    if st.button("Review GitHub Repository"):
        # Clear previous chat cache and history
        try:
            requests.post("http://127.0.0.1:8000/clear-chat")
        except Exception:
            pass
        st.session_state["zip_chat_history"] = []
        st.session_state["zip_button_answer"] = None
        st.session_state["zip_button_question"] = None
        st.session_state["github_chat_history"] = []
        st.session_state["github_button_answer"] = None
        st.session_state["github_button_question"] = None
        st.session_state["chat_history"] = []
        st.session_state["chat_cache"] = {}
        st.session_state["current_report_hash"] = None
        st.session_state["review_context"] = None
        st.session_state["open_ai_assistant"] = False
        st.session_state.pop("review_result", None)
        st.session_state.pop("report", None)

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
                    st.session_state["review_result"] = result
                    st.session_state["report"] = result["report"]
                    st.session_state["open_ai_assistant"] = True
                    st.session_state["review_context"] = result.get("review_context")
                    st.session_state["tab"] = "github"
                    st.session_state["zip_chat_history"] = []
                    st.session_state["zip_button_answer"] = None
                    st.session_state["zip_button_question"] = None
                    st.session_state["github_chat_history"] = []
                    st.session_state["github_button_answer"] = None
                    st.session_state["github_button_question"] = None
                    st.session_state["chat_history"] = []
                    st.session_state["chat_cache"] = {}
                    st.session_state["current_report_hash"] = None
                    st.success("Repository review completed successfully!")
                else:
                    st.error(response.text)

    # Render report if it is in session state for github tab
    if st.session_state.get("review_result") and st.session_state.get("tab") == "github":
        result = st.session_state["review_result"]
        st.info(f"Report generated: {result['report_file']}")

        with st.expander("📄 View Report"):
            st.markdown(result["report"])

        download_url = f"http://127.0.0.1:8000/download-report/{result['report_file']}"
        pdf_url = f"http://127.0.0.1:8000/download-pdf/{result['pdf_file']}"

        st.markdown("")

        space1, btn1, gap, btn2, space2 = st.columns(
            [1, 2, 0.5, 2, 1]
        )

        with btn1:
            st.link_button(
                "⬇️ Download Markdown",
                download_url,
                use_container_width=True
            )

        with btn2:
            st.link_button(
                "📄 Download PDF",
                pdf_url,
                use_container_width=True
            )
            
        # Chat expander
        st.markdown("---")
        if "github_chat_history" not in st.session_state:
            st.session_state["github_chat_history"] = []
        if "github_button_answer" not in st.session_state:
            st.session_state["github_button_answer"] = None
        if "github_button_question" not in st.session_state:
            st.session_state["github_button_question"] = None

        with st.expander("AI Review Assistant",
            expanded=st.session_state.get(
                "open_ai_assistant",
                False
            )
        ):
            st.write("###  AI Review Assistant")
            st.markdown("---")
            
            # Render conversation history (if active)
            if st.session_state["github_chat_history"]:
                st.markdown("#### Custom Q&A Chat")
                for msg in st.session_state["github_chat_history"]:
                    if msg["role"] == "user":
                        st.write(f" **You:** {msg['content']}")
                    else:
                        st.info(f" **Assistant:** {msg['content']}")
                st.markdown("---")
            
            # Render single button response (if active)
            if st.session_state["github_button_answer"]:
                st.markdown(f"**Quick Section Guide:** **{st.session_state['github_button_question']}**")
                st.info(st.session_state["github_button_answer"])
                st.markdown("---")
            
            # Predefined question buttons
            col_c1, col_c2, col_c3 = st.columns(3)
            col_c4, col_c5, col_c6 = st.columns(3)
            
            predefined_question = None
            display_question = None
            
            with col_c1:
                if st.button("🔍 Explain Critical Issues", key="github_btn1"):
                    predefined_question = "Explain the critical issues found in this review. For each issue explain:\n- why it occurs\n- possible impact\n- risk severity\n- recommended fix\n\nUse only findings present in the review.\nMaximum 150 words."
                    display_question = "Explain Critical Issues"
            with col_c2:
                if st.button("⚠️ What Should I Fix First?", key="github_btn2"):
                    predefined_question = "Based only on the review findings, prioritize all issues from highest risk to lowest risk.\n\nExplain:\n- what should be fixed first\n- why it is highest priority\n- recommended order of implementation\n\nMaximum 150 words."
                    display_question = "What Should I Fix First?"
            with col_c3:
                if st.button("🛡️ Explain Security Risks", key="github_btn3"):
                    predefined_question = "Explain only the security findings identified in the review.\n\nInclude:\n- security risk\n- attack impact\n- business impact\n- recommended remediation\n\nUse only findings present in the review.\n\nMaximum 150 words."
                    display_question = "Explain Security Risks"
            with col_c4:
                if st.button("📋 Summarize Report", key="github_btn4"):
                    predefined_question = "Provide a concise executive summary of the review.\n\nInclude:\n- overall project health\n- major findings\n- release readiness\n\nMaximum 150 words."
                    display_question = "Summarize Report"
            with col_c5:
                if st.button("🏗️ Explain Architecture Analysis", key="github_btn5"):
                    predefined_question = "Explain the architecture analysis section.\n\nInclude:\n- detected project structure\n- architecture observations\n- actual risks identified\n\nIf no architecture risks exist, explain why the architecture appears acceptable.\n\nMaximum 150 words."
                    display_question = "Explain Architecture Analysis"
            with col_c6:
                if st.button("📦 Explain Dependency Security Analysis", key="github_btn6"):
                    predefined_question = "Explain the dependency security analysis findings.\n\nIf vulnerable dependencies exist:\n- explain risks\n- explain impact\n- recommend upgrades\n\nIf no vulnerable dependencies exist:\n- explain that dependency health appears acceptable\n\nMaximum 150 words."
                    display_question = "Explain Dependency Security Analysis"
            
            with st.form("github_chat_form", clear_on_submit=False):
                    # Custom input
                    custom_question = st.text_input(
                        "Ask a question about this review...",
                        placeholder="Ask a question about this review...",
                        key="github_custom_input"
                    )
                
                    # Ask button
                    ask_clicked = st.form_submit_button("Ask")

            question_to_submit = None
            
            if predefined_question:
                question_to_submit = predefined_question
            elif ask_clicked and custom_question:
                display_question = custom_question
                question_to_submit = custom_question
                
            if question_to_submit:
                with st.spinner("Thinking..."):
                    try:
                        if predefined_question:
                            def stream_github_button():
                                resp = requests.post(
                                    "http://127.0.0.1:8000/ask-review-stream",
                                    json={
                                        "report": result["report"],
                                        "question": question_to_submit,
                                        "history": [],
                                        "review_context": st.session_state.get("review_context")
                                    },
                                    stream=True
                                )
                                for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                                    if chunk:
                                        yield chunk
                                        
                            answer = st.write_stream(stream_github_button())
                            st.session_state["github_button_answer"] = answer
                            st.session_state["github_button_question"] = display_question
                            st.session_state["open_ai_assistant"] = True
                            st.rerun()
                        elif ask_clicked and custom_question:
                            history_payload = st.session_state["github_chat_history"][-5:]
                            def stream_github_custom():
                                resp = requests.post(
                                    "http://127.0.0.1:8000/ask-review-stream",
                                    json={
                                        "report": result["report"],
                                        "question": question_to_submit,
                                        "history": history_payload,
                                        "review_context": st.session_state.get("review_context")
                                    },
                                    stream=True
                                )
                                for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                                    if chunk:
                                        yield chunk
                                        
                            answer = st.write_stream(stream_github_custom())
                            st.session_state["github_button_answer"] = None # Custom clears button answer
                            st.session_state["github_button_question"] = None
                            st.session_state["github_chat_history"].append({"role": "user", "content": display_question})
                            st.session_state["github_chat_history"].append({"role": "assistant", "content": answer})
                            st.session_state["open_ai_assistant"] = True
                            st.rerun()
                    except Exception as e:
                        st.error(f"Failed to connect to backend: {e}")