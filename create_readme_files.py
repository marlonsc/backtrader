#!/usr/bin/env python3
"""Script to create README.md files for all directories in the repository.

This script recursively traverses the repository and creates a README.md file
for each directory, with links to parent directories and subdirectories."""
"""

import os
import sys
import glob
import re
from collections import defaultdict

# Root directory of the repository
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

def get_file_description(file_path):
"""Extract a description from a file based on its content and type.
    
Args::
        file_path: Path to the file
        
Returns::
        A string description of the file"""
    """
    if not os.path.isfile(file_path):
        return "Directory"
    
    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    # Default description
    description = ""
    
    try:
        # For Python files, try to extract docstring
        if ext == '.py':
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
                # Try to find module docstring
                module_docstring = re.search(r'"""(.*?)"""', content, re.DOTALL)
                if module_docstring:
                    # Extract first line or first sentence of docstring
                    docstring = module_docstring.group(1).strip()
                    first_line = docstring.split('\n')[0].strip()
                    if first_line:
                        description = first_line
                    else:
                        # If first line is empty, try to get the first non-empty line
                        for line in docstring.split('\n'):
                            if line.strip():
                                description = line.strip()
                                break
                
                # If no docstring found, try to infer from class or function definitions
                if not description:
                    class_match = re.search(r'class\s+(\w+).*?:.*?"""(.*?)"""', content, re.DOTALL)
                    if class_match:
                        class_name = class_match.group(1)
                        class_desc = class_match.group(2).strip().split('\n')[0].strip()
                        description = f"{class_name}: {class_desc}"
        
        # For other file types, provide a generic description based on file type
        elif ext in ['.c', '.cpp', '.h', '.hpp']:
            description = "C/C++ source code file"
        elif ext == '.md':
            description = "Markdown documentation file"
        elif ext == '.rst':
            description = "reStructuredText documentation file"
        elif ext == '.txt':
            description = "Text file"
        elif ext == '.json':
            description = "JSON data file"
        elif ext == '.yml' or ext == '.yaml':
            description = "YAML configuration file"
        elif ext == '.sh':
            description = "Shell script"
        elif ext == '.bat':
            description = "Windows batch file"
        elif ext == '.css':
            description = "CSS stylesheet"
        elif ext == '.js':
            description = "JavaScript file"
        elif ext == '.html':
            description = "HTML file"
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        description = f"File with {ext} extension"
    
    return description if description else f"File with {ext} extension"

def create_readme(directory):
"""Create a README.md file for the given directory.
    
Args::
        directory: Path to the directory"""
    """
    # Skip if directory is a hidden directory or contains specific patterns to ignore
    dir_name = os.path.basename(directory)
    if dir_name.startswith('.') or dir_name in ['__pycache__', 'node_modules', 'venv', 'env', '.git']:
        return
    
    readme_path = os.path.join(directory, 'README.md')
    
    # Get directory name and create a title
    dir_name = os.path.basename(directory)
    title = dir_name.replace('_', ' ').title()
    
    # Create content for README.md
    content = [f"# {title}\n"]
    
    # Add description based on directory content
    description = "This directory contains "
    
    # Count file types
    file_types = defaultdict(int)
    for file_path in glob.glob(os.path.join(directory, '*')):
        if os.path.isfile(file_path):
            _, ext = os.path.splitext(file_path)
            if ext:
                file_types[ext.lower()] += 1
    
    if file_types:
        file_type_desc = ", ".join([f"{count} {ext[1:]} file{'s' if count > 1 else ''}" for ext, count in file_types.items()])
        description += f"various files including {file_type_desc}."
    else:
        description += "subdirectories and files related to the project."
    
    content.append(f"{description}\n")
    
    # Add navigation links
    content.append("## Navigation\n")
    
    # Link to root directory
    rel_path_to_root = os.path.relpath(ROOT_DIR, directory)
    content.append(f"* [🏠 Root Directory]({rel_path_to_root}/README.md)")
    
    # Link to parent directory if not root
    if directory != ROOT_DIR:
        parent_dir = os.path.dirname(directory)
        parent_name = os.path.basename(parent_dir)
        rel_path_to_parent = os.path.relpath(parent_dir, directory)
        content.append(f"* [⬆️ Parent Directory ({parent_name})]({rel_path_to_parent}/README.md)")
    
    content.append("")
    
    # Add subdirectories section
    subdirs = [d for d in glob.glob(os.path.join(directory, '*')) if os.path.isdir(d) and not os.path.basename(d).startswith('.')]
    if subdirs:
        content.append("### Subdirectories\n")
        for subdir in sorted(subdirs):
            subdir_name = os.path.basename(subdir)
            if not subdir_name.startswith('.') and subdir_name not in ['__pycache__', 'node_modules', 'venv', 'env', '.git']:
                content.append(f"* [{subdir_name}]({subdir_name}/README.md)")
        content.append("")
    
    # Add files section
    files = [f for f in glob.glob(os.path.join(directory, '*')) if os.path.isfile(f) and os.path.basename(f) != 'README.md']
    if files:
        content.append("## Files\n")
        for file_path in sorted(files):
            file_name = os.path.basename(file_path)
            description = get_file_description(file_path)
            content.append(f"### {file_name}\n")
            content.append(f"{description}\n")
    
    # Add directory summary
    file_count = len(files)
    subdir_count = len(subdirs)
    content.append("## Directory Summary\n")
    content.append(f"This directory contains {file_count} file{'s' if file_count != 1 else ''} and {subdir_count} subdirector{'ies' if subdir_count != 1 else 'y'}.\n")
    
    # Add file type summary
    if file_types:
        content.append("### File Types\n")
        for ext, count in sorted(file_types.items()):
            content.append(f"* {ext}: {count} file{'s' if count > 1 else ''}")
        content.append("")
    
    # Write content to README.md
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"Created README.md for {directory}")

def process_directory(directory):
"""Process a directory and its subdirectories recursively.
    
Args::
        directory: Path to the directory"""
    """
    create_readme(directory)
    
    # Process subdirectories
    for subdir in glob.glob(os.path.join(directory, '*')):
        if os.path.isdir(subdir) and not os.path.basename(subdir).startswith('.') and os.path.basename(subdir) not in ['__pycache__', 'node_modules', 'venv', 'env', '.git']:
            process_directory(subdir)

if __name__ == '__main__':
    print(f"Creating README.md files for all directories in {ROOT_DIR}")
    process_directory(ROOT_DIR)
    print("Done!")