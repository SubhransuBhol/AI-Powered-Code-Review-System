from langchain_ollama import OllamaLLM
import time

llm = OllamaLLM(
    model="qwen2.5-coder:7b",
    temperature=0.2,
    options={
        "num_predict": 512,
        "temperature": 0.2
    }
)

def generate_master_review(summary_text):

    prompt = f"""
You are a senior software architect. Analyze this project code review summary and generate five specific sections.

Rules:
1. Do NOT write any introduction, pleasantries, or filler text. Start directly with the markdown format below.
2. Keep each section extremely brief (maximum 2-3 sentences or bullet points).
3. Do NOT invent new bugs or speculate. Summarize only from the provided metrics.

Format the output EXACTLY as follows:

## Executive Assessment
* [Your high-level assessment of the code quality, architecture, and overall project health]

## Strengths
* [Identify 1-2 major strengths of the code, e.g. modularity, zero critical bugs, structure]

## Weaknesses
* [Identify 1-2 major weaknesses of the code, e.g. quality issues, security exposure]

## Security Assessment
* [Your assessment of the project's security posture based on the security findings and risk level]

## Final Verdict
* [Your final release recommendation: e.g. Approved, Conditional Approval, or Rejected, with a brief explanation]

Project Summary Metrics:
{summary_text}
"""

    input_len = len(prompt)
    print(f"MASTER INPUT LENGTH: {input_len}")

    start = time.time()
    result = llm.invoke(prompt)
    duration = time.time() - start

    output_len = len(result)
    print(f"MASTER OUTPUT LENGTH: {output_len}")
    print(f"MASTER RAW GENERATION: {round(duration, 2)} sec")
    print(f"MASTER TOTAL TIME: {round(duration, 2)} sec")

    return result