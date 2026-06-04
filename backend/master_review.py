from langchain_ollama import OllamaLLM
import time

llm = OllamaLLM(
    model="qwen2.5-coder:7b",
    temperature=0.2,
    options={
        "num_predict": 256,
        "temperature": 0.2
    }
)

def generate_master_review(summary_text):

    prompt = f"""
You are a senior software architect. Analyze this project code review summary and generate three specific sections.

Rules:
1. Do NOT write any introduction, pleasantries, or filler text. Start directly with the markdown format below.
2. Keep each section extremely brief (maximum 2-3 sentences or bullet points).
3. Do NOT invent new bugs or speculate. Summarize only from the provided metrics.

Format the output EXACTLY as follows:

## Executive Assessment
* [Your high-level assessment of the code quality, architecture, and overall project health]

## Security Assessment
* [Your assessment of the project's security posture based on the security findings and risk level]

## Final Verdict
* [Your final release recommendation: e.g. Approved, Conditional Approval, or Rejected, with a brief explanation]

Project Summary Metrics:
{summary_text}
"""

    print(
        "MASTER INPUT LENGTH:",
        len(prompt)
    )

    start = time.time()

    result = llm.invoke(prompt)

    print(
        "MASTER OUTPUT LENGTH:",
        len(result)
    )

    print(
        "MASTER RAW GENERATION:",
        round(time.time() - start, 2),
        "sec"
    )

    return result