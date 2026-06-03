from langchain_ollama import OllamaLLM
from utils.file_reader import get_project_files
from utils.report_saver import save_report
import time

# Configurable constants
MAX_FILE_LINES = 200

# Create OllamaLLM instance once at module level and reuse it
llm = OllamaLLM(
    model="qwen2.5-coder:7b",
    temperature=0.2,
    options={
        "num_predict": 3072,
        "temperature": 0.2
    }
)

def review_multiple_files(files):
    """
    Reviews multiple files in a single LLM prompt invocation.
    
    Args:
        files (list): A list of dictionaries containing filename and content:
            [
                {
                    "filename": "...",
                    "content": "..."
                }
            ]
            
    Returns:
        str: The generated review report.
    """
    code_blocks = ""
    for file in files:
        filename = file["filename"]
        content = file["content"]
        
        # Truncate extremely large file contents based on line count limit
        lines = content.splitlines()
        if len(lines) > MAX_FILE_LINES:
            content = "\n".join(lines[:MAX_FILE_LINES]) + f"\n\n# ... [Rest of the file truncated to first {MAX_FILE_LINES} lines due to size limits] ...\n"
            
        code_blocks += f"\n--- File: {filename} ---\n{content}\n"
        
        prompt = f"""
        You are a senior software engineer.

        Review the following files. For each file, identify bugs, security issues, and improvements.

        IMPORTANT RULES:
        1. Do NOT invent bugs.
        2. Do NOT guess missing code.
        3. Do NOT assume functionality that is not present.
        4. If an issue is not explicitly visible in the code, do not mention it.
        5. Do not provide code examples.
        6. Keep each section under 3 bullet points.
        7. If no issues exist write:
        - None
        8. Treat each file completely independently. Do NOT mix issues from one file into another. For example, if a security issue exists in auth.py, do NOT mention it under database.py or calculator.py unless it is explicitly present in database.py or calculator.py.

        For each file, you MUST format the review EXACTLY as follows:

        # File Review: [filename]

        ## Bugs
        - ...

        ## Security Issues
        - ...

        ## Improvements
        - ...

        Files:
        {code_blocks}
    """
    start_time = time.time()
    response = llm.invoke(prompt)
    print(f"Ollama Multi-file LLM Call Time: {time.time() - start_time:.2f} sec")
    return response

if __name__ == "__main__":
    print("Running standalone repository-level review...")
    # Load files from sample project
    project_files = get_project_files("../sample_project")
    
    # Format files for the function
    formatted_files = [{"filename": f["filename"], "content": f["content"]} for f in project_files]
    
    # Run the repository review in exactly one LLM call
    report = review_multiple_files(formatted_files)
    
    # Save the report
    saved_file = save_report(report)
    print("\n--- Generated Report ---")
    print(report)
    print(f"\nReport successfully saved to: {saved_file}")
