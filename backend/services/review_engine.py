from langchain_ollama import OllamaLLM
import time

llm = OllamaLLM(
    model="qwen2.5-coder:7b",
    temperature=0.0,
    options={
        "num_predict": 512,
        "temperature": 0.0
    }
)

def review_single_file(filename, content):
    prompt = f"""
Review this file.

Return ONLY:

## Bugs
* ...

## Security Issues
* ...

## Improvements
* ...

Rules:
* Report only issues visible in the code.
* Do not invent bugs.
* Do not invent security issues.
* If an issue exists, explain it in one sentence.
* Maximum 5 bullet points per section.
* Only report issues that are explicitly visible in the code.
* Do not speculate.
* For each section:
    - If issues exist, list them.
    - If no issues exist, write:
  None
* Do not infer missing functionality.
* Do not report missing security features.
    Examples:
    - rate limiting
    - logging
    - MFA
    - CAPTCHA
    - password complexity checks
    - monitoring
* A bug must cause:
    - incorrect behavior
    - incorrect output
    - crashes
    - exceptions
    - security vulnerabilities  

Do not classify missing best practices as bugs.
unless the absence directly creates a visible vulnerability.
* Do not assume future requirements.
* If an issue is uncertain, do not report it.

Code:
{content}
"""

    start = time.time()

    response = llm.invoke(prompt)

    print(
        f"LLM Call Time: {time.time()-start:.2f} sec"
    )

    return response
