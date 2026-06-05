import re
from difflib import SequenceMatcher

MIN_LINES = 10

def clean_code_lines(content):
    cleaned_lines = []
    for line in content.splitlines():
        # Remove line-level comments
        no_comment = line.split('#', 1)[0]
        no_comment = no_comment.split('//', 1)[0]
        
        stripped = no_comment.strip()
        # Normalize whitespace (replace multiple spaces/tabs with single space)
        normalized = re.sub(r'\s+', ' ', stripped)
        if normalized:
            cleaned_lines.append(normalized)
    return cleaned_lines

def detect_duplicates(files_dict):
    """
    files_dict: dict of {filename: content}
    Returns a list of duplicate dicts with similarity >= 0.85.
    """
    cleaned_contents = {}
    
    for name, content in files_dict.items():
        lines = clean_code_lines(content)
        # Skip files with fewer than 10 non-empty cleaned lines
        if len(lines) >= MIN_LINES:
            cleaned_contents[name] = "\n".join(lines)
            
    filenames_to_compare = list(cleaned_contents.keys())
    duplicates = []
    n = len(filenames_to_compare)
    
    for i in range(n):
        for j in range(i + 1, n):
            file1 = filenames_to_compare[i]
            file2 = filenames_to_compare[j]
            
            c1 = cleaned_contents[file1]
            c2 = cleaned_contents[file2]
            
            matcher = SequenceMatcher(None, c1, c2)
            ratio = matcher.ratio()
            
            if ratio >= 0.85:
                duplicates.append({
                    "file1": file1,
                    "file2": file2,
                    "similarity": int(round(ratio * 100))
                })
    return duplicates

def generate_duplicate_report_section(duplicates):
    section = "## Duplicate Code Analysis\n"
    if duplicates:
        for dup in duplicates:
            # Using standard bullet points (*) and standard ASCII - symbol (no unicode ↔)
            section += f"* {dup['file1']} - {dup['file2']} ({dup['similarity']}% similar)\n"
        section += "\nRecommendation:\nExtract repeated logic into shared functions, classes, or utility modules."
    else:
        section += "* No significant duplicate code detected."
    return section
