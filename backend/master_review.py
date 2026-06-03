from langchain_ollama import OllamaLLM

llm = OllamaLLM(
    model="qwen2.5-coder:7b",
    temperature=0.2,
    options={
        "num_predict": 1024,
        "temperature": 0.2
    }
)

def generate_master_review(all_reviews):

    prompt = f"""
You are a senior software architect.

Analyze these file reviews.

Generate a professional project report.

Include:

1. Project Overview
2. Critical Issues
3. Security Risks
4. Code Quality Score (out of 10)
5. Recommendations
6. Final Verdict

Reviews:

{all_reviews}
"""

    return llm.invoke(prompt)