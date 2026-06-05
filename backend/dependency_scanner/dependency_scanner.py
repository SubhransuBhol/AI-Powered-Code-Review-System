import re
import json
from dependency_scanner.vulnerable_packages import PYTHON_RULES, NPM_RULES

def parse_version(version_str):
    if not version_str:
        return None
    # Check if the cleaned version string contains any digits.
    # If not, it's a dynamic specifier like '*' or 'latest', so skip/return None
    cleaned = re.sub(r'^[v\^~>=<!\s]+', '', version_str).strip()
    if not any(c.isdigit() for c in cleaned):
        return None
        
    version_str = cleaned
    # Take only the first part before any '-' or '+' or space
    version_str = re.split(r'[-+\s]', version_str)[0]
    parts = []
    for part in version_str.split('.'):
        match = re.match(r'^(\d+)', part)
        if match:
            parts.append(int(match.group(1)))
        else:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def scan_requirements_txt(content):
    findings = []
    for line in content.splitlines():
        line = line.split('#')[0].split(';')[0].strip()
        if not line:
            continue
        if '==' in line:
            parts = line.split('==')
            if len(parts) == 2:
                pkg = parts[0].strip().lower()
                ver_str = parts[1].strip()
                if pkg in PYTHON_RULES:
                    ver = parse_version(ver_str)
                    if ver is not None:
                        rule = PYTHON_RULES[pkg]
                        if ver < rule["vulnerable_below"]:
                            findings.append({
                                "package": parts[0].strip(),
                                "version": ver_str,
                                "risk_type": "Security Risk",
                                "severity": "HIGH",
                                "message": "Known vulnerable version detected."
                            })
                        elif ver < rule["outdated_below"]:
                            findings.append({
                                "package": parts[0].strip(),
                                "version": ver_str,
                                "risk_type": "Maintenance Risk",
                                "severity": "LOW",
                                "message": "Outdated version detected."
                            })
    return findings

def scan_package_json(content):
    findings = []
    try:
        data = json.loads(content)
    except Exception:
        return findings
    
    for key in ["dependencies", "devDependencies"]:
        dep_dict = data.get(key, {})
        if not isinstance(dep_dict, dict):
            continue
        for pkg, ver_str in dep_dict.items():
            pkg_lower = pkg.lower()
            if pkg_lower in NPM_RULES:
                if isinstance(ver_str, str):
                    ver = parse_version(ver_str)
                    if ver is not None:
                        rule = NPM_RULES[pkg_lower]
                        if ver < rule["vulnerable_below"]:
                            findings.append({
                                "package": pkg,
                                "version": ver_str,
                                "risk_type": "Security Risk",
                                "severity": "HIGH",
                                "message": "Known vulnerable version detected."
                            })
                        elif ver < rule["outdated_below"]:
                            findings.append({
                                "package": pkg,
                                "version": ver_str,
                                "risk_type": "Maintenance Risk",
                                "severity": "LOW",
                                "message": "Outdated version detected."
                            })
    return findings

def scan_package_lock_json(content):
    findings = []
    try:
        data = json.loads(content)
    except Exception:
        return findings
    
    seen_pkg_versions = set()
    
    # 1. Packages section (v2/v3 lockfile format)
    packages_dict = data.get("packages", {})
    if isinstance(packages_dict, dict):
        for path, info in packages_dict.items():
            if not isinstance(info, dict):
                continue
            if "node_modules/" in path:
                pkg = path.split("node_modules/")[-1]
            else:
                pkg = path
            if not pkg:
                continue
            
            ver_str = info.get("version")
            if pkg and isinstance(ver_str, str):
                pkg_lower = pkg.lower()
                if pkg_lower in NPM_RULES:
                    key = (pkg_lower, ver_str)
                    if key not in seen_pkg_versions:
                        seen_pkg_versions.add(key)
                        ver = parse_version(ver_str)
                        if ver is not None:
                            rule = NPM_RULES[pkg_lower]
                            if ver < rule["vulnerable_below"]:
                                findings.append({
                                    "package": pkg,
                                    "version": ver_str,
                                    "risk_type": "Security Risk",
                                    "severity": "HIGH",
                                    "message": "Known vulnerable version detected."
                                })
                            elif ver < rule["outdated_below"]:
                                findings.append({
                                    "package": pkg,
                                    "version": ver_str,
                                    "risk_type": "Maintenance Risk",
                                    "severity": "LOW",
                                    "message": "Outdated version detected."
                                })
                                
    # 2. Dependencies section (v1 lockfile format)
    dependencies_dict = data.get("dependencies", {})
    if isinstance(dependencies_dict, dict):
        def traverse_deps(deps):
            for pkg, info in deps.items():
                if not isinstance(info, dict):
                    continue
                ver_str = info.get("version")
                if isinstance(ver_str, str):
                    pkg_lower = pkg.lower()
                    if pkg_lower in NPM_RULES:
                        key = (pkg_lower, ver_str)
                        if key not in seen_pkg_versions:
                            seen_pkg_versions.add(key)
                            ver = parse_version(ver_str)
                            if ver is not None:
                                rule = NPM_RULES[pkg_lower]
                                if ver < rule["vulnerable_below"]:
                                    findings.append({
                                        "package": pkg,
                                        "version": ver_str,
                                        "risk_type": "Security Risk",
                                        "severity": "HIGH",
                                        "message": "Known vulnerable version detected."
                                    })
                                elif ver < rule["outdated_below"]:
                                    findings.append({
                                        "package": pkg,
                                        "version": ver_str,
                                        "risk_type": "Maintenance Risk",
                                        "severity": "LOW",
                                        "message": "Outdated version detected."
                                    })
                nested_deps = info.get("dependencies", {})
                if isinstance(nested_deps, dict) and nested_deps:
                    traverse_deps(nested_deps)
        
        traverse_deps(dependencies_dict)
        
    return findings

def scan_project_dependencies(files_dict):
    """
    Scans files_dict (dict of {filename: content}) for requirements.txt, package.json, and package-lock.json.
    Returns: (manifests_found: bool, findings: list)
    """
    manifests_found = False
    all_findings = []
    
    for filename, content in files_dict.items():
        base = filename.replace("\\", "/").split('/')[-1]
        if base == "requirements.txt":
            manifests_found = True
            all_findings.extend(scan_requirements_txt(content))
        elif base == "package.json":
            manifests_found = True
            all_findings.extend(scan_package_json(content))
        elif base == "package-lock.json":
            manifests_found = True
            all_findings.extend(scan_package_lock_json(content))
            
    # Deduplicate findings
    seen = set()
    deduped_findings = []
    for f in all_findings:
        key = (f["package"].lower(), f["version"], f["risk_type"])
        if key not in seen:
            seen.add(key)
            deduped_findings.append(f)
            
    return manifests_found, deduped_findings

def generate_dependency_report_section(manifests_found, findings):
    section = "## Dependency Security Analysis\n"
    if not manifests_found:
        section += "\n* No dependency manifest files detected."
    elif not findings:
        section += "\n* No vulnerable dependencies detected."
    else:
        for f in findings:
            section += f"\n* [{f['severity']}] {f['package']}=={f['version']}\n"
            section += f"  {f['risk_type']}: {f['message']}\n"
        section += "\nRecommendation:\n\n* Upgrade vulnerable and outdated dependencies to supported versions."
    return section
