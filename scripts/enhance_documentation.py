#!/usr/bin/env python3
"""Documentation Enhancement Script for Backtrader Repository
This script enhances the existing README.md files with more detailed documentation,
improves code documentation, and creates links between directories.
Usage:
python enhance_documentation.py
Author: OpenHands AI"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import ast
import inspect

# Directories to exclude from documentation
EXCLUDE_DIRS = {
    '.git', '__pycache__', '.github', 'venv', 'env', '.venv', '.env',
    'node_modules', 'dist', 'build', '.idea', '.vscode', '.pytest_cache'
}

# Files to exclude from documentation
EXCLUDE_FILES = {
    '.gitignore', '.gitattributes', '.DS_Store', 'Thumbs.db', '.env',
    '.editorconfig', '.prettierrc', '.eslintrc', '.babelrc', '.dockerignore',
    'package-lock.json', 'yarn.lock', 'poetry.lock', 'Pipfile.lock'
}

def translate_to_english(text: str) -> str:
"""Translate non-English text to English.
    
Args::
        text: Text to translate
        
Returns::
        Translated text"""
    """
    # Portuguese to English translations
    pt_to_en = {
        'faça': 'do',
        'está': 'is',
        'função': 'function',
        'variáveis': 'variables',
        'para o': 'for the',
        'como um': 'as a',
        'não é': 'is not',
        'utilitários': 'utilities',
        'notificação': 'notification',
        'adicione': 'add',
        'exemplo': 'example',
        'iniciando': 'starting',
        'testando': 'testing',
        'executa': 'executes',
        'combinações': 'combinations',
        'padrão': 'default',
        'estratégias': 'strategies',
        'arbitragem': 'arbitrage'
    }
    
    # German to English translations
    de_to_en = {
        'wenn': 'if',
        'hier': 'here',
        'wird': 'becomes',
        'noch': 'still',
        'bereits': 'already',
        'ganz': 'completely',
        'blöde': 'stupid',
        'idee': 'idea',
        'formulierung': 'formulation',
        'äquivalent': 'equivalent',
        'markt': 'market',
        'daten': 'data',
        'werte': 'values',
        'berechnung': 'calculation',
        'beispiel': 'example',
        'ausgabe': 'output',
        'erstelle': 'create',
        'kauf': 'buy',
        'verkauf': 'sell',
        'verfolge': 'track',
        'bestellung': 'order'
    }
    
    # Apply translations
    translated = text
    
    # Portuguese translations
    for pt, en in pt_to_en.items():
        translated = re.sub(r'\b' + pt + r'\b', en, translated, flags=re.IGNORECASE)
    
    # German translations
    for de, en in de_to_en.items():
        translated = re.sub(r'\b' + de + r'\b', en, translated, flags=re.IGNORECASE)
    
    # Handle Chinese characters
    if re.search(r'[\u4e00-\u9fff]', text):
        # For now, just note that there are Chinese characters
        # In a real implementation, you would use a translation service
        translated += " [Contains Chinese characters that should be translated]"
    
    return translated

def analyze_python_file(file_path: str) -> Dict:
"""Analyze a Python file to extract classes, functions, and docstrings.
    
Args::
        file_path: Path to the Python file
        
Returns::
        Dictionary containing file information"""
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Parse the Python file
        tree = ast.parse(content)
        
        # Extract module docstring
        module_docstring = ast.get_docstring(tree)
        
        # Extract classes and functions
        classes = []
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'docstring': ast.get_docstring(node) or '',
                    'methods': []
                }
                
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        method_info = {
                            'name': child.name,
                            'docstring': ast.get_docstring(child) or ''
                        }
                        class_info['methods'].append(method_info)
                
                classes.append(class_info)
            
            elif isinstance(node, ast.FunctionDef) and node.parent_field != 'body':
                function_info = {
                    'name': node.name,
                    'docstring': ast.get_docstring(node) or ''
                }
                functions.append(function_info)
        
        return {
            'module_docstring': module_docstring or '',
            'classes': classes,
            'functions': functions
        }
    
    except Exception as e:
        print(f"Error analyzing {file_path}: {str(e)}")
        return {
            'module_docstring': '',
            'classes': [],
            'functions': []
        }

def enhance_readme(directory: str) -> None:
"""Enhance the README.md file for the specified directory.
    
Args::
        directory: Path to the directory"""
    """
    readme_path = os.path.join(directory, "README.md")
    
    # Skip if README.md doesn't exist
    if not os.path.exists(readme_path):
        return
    
    # Read existing README.md
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract directory name
    dir_name = os.path.basename(directory)
    
    # Get all files in the directory
    files = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path) and item not in EXCLUDE_FILES and not item.startswith('.'):
            files.append(item)
    
    # Sort files alphabetically
    files.sort()
    
    # Analyze Python files
    python_files = {}
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(directory, file)
            python_files[file] = analyze_python_file(file_path)
    
    # Create enhanced README content
    enhanced_content = []
    
    # Add header
    enhanced_content.append(f"# {dir_name}\n\n")
    
    # Extract existing description
    description_match = re.search(r'# .*?\n\n(.*?)\n\n', content, re.DOTALL)
    if description_match:
        description = description_match.group(1)
        enhanced_content.append(f"{description}\n\n")
    else:
        enhanced_content.append("This directory contains files related to the Backtrader trading framework.\n\n")
    
    # Add navigation section
    enhanced_content.append("## Navigation\n\n")
    
    # Add link to root directory
    root_path = os.path.relpath('/workspace/backtrader', directory)
    enhanced_content.append(f"* [🏠 Root Directory]({root_path}/README.md)\n")
    
    # Add link to parent directory
    parent_dir = os.path.dirname(directory)
    if parent_dir and parent_dir != '/workspace/backtrader':
        parent_name = os.path.basename(parent_dir)
        enhanced_content.append(f"* [⬆️ Parent Directory ({parent_name})]({os.path.relpath(parent_dir, directory)}/README.md)\n")
    
    # Add links to subdirectories
    subdirs = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path) and item not in EXCLUDE_DIRS and not item.startswith('.'):
            subdirs.append(item)
    
    if subdirs:
        enhanced_content.append("\n### Subdirectories\n\n")
        for subdir in sorted(subdirs):
            subdir_readme = os.path.join(directory, subdir, "README.md")
            if os.path.exists(subdir_readme):
                # Extract description from subdir README
                with open(subdir_readme, 'r', encoding='utf-8') as f:
                    subdir_content = f.read()
                    subdir_desc_match = re.search(r'# .*?\n\n(.*?)\n\n', subdir_content, re.DOTALL)
                    if subdir_desc_match:
                        subdir_desc = subdir_desc_match.group(1).split('.')[0]
                    else:
                        subdir_desc = f"Directory containing {subdir} related files"
            else:
                subdir_desc = f"Directory containing {subdir} related files"
            
            enhanced_content.append(f"* [{subdir}]({subdir}/README.md) - {subdir_desc}\n")
    
    # Add detailed file documentation
    if files:
        enhanced_content.append("\n## Files\n\n")
        
        for file in files:
            enhanced_content.append(f"### {file}\n\n")
            
            if file.endswith('.py'):
                # Add Python file documentation
                file_info = python_files.get(file, {})
                module_docstring = file_info.get('module_docstring', '')
                
                if module_docstring:
                    # Extract first paragraph of docstring
                    first_para = module_docstring.split('\n\n')[0].strip()
                    enhanced_content.append(f"{first_para}\n\n")
                
                # List classes and functions
                classes = file_info.get('classes', [])
                functions = file_info.get('functions', [])
                
                if classes:
                    enhanced_content.append("**Classes:**\n\n")
                    for cls in classes:
                        cls_name = cls.get('name', '')
                        cls_docstring = cls.get('docstring', '')
                        
                        if cls_docstring:
                            # Extract first line of docstring
                            cls_desc = cls_docstring.split('\n')[0].strip()
                            enhanced_content.append(f"* `{cls_name}`: {cls_desc}\n")
                        else:
                            enhanced_content.append(f"* `{cls_name}`\n")
                    
                    enhanced_content.append("\n")
                
                if functions:
                    enhanced_content.append("**Functions:**\n\n")
                    for func in functions:
                        func_name = func.get('name', '')
                        func_docstring = func.get('docstring', '')
                        
                        if func_docstring:
                            # Extract first line of docstring
                            func_desc = func_docstring.split('\n')[0].strip()
                            enhanced_content.append(f"* `{func_name}`: {func_desc}\n")
                        else:
                            enhanced_content.append(f"* `{func_name}`\n")
                    
                    enhanced_content.append("\n")
            else:
                # For non-Python files, extract description from existing README
                file_section_match = re.search(f"### {re.escape(file)}\\s*\\n\\n(.*?)\\n\\n", content, re.DOTALL)
                if file_section_match:
                    file_desc = file_section_match.group(1)
                    enhanced_content.append(f"{file_desc}\n\n")
                else:
                    enhanced_content.append(f"File with {os.path.splitext(file)[1]} extension.\n\n")
    
    # Add directory summary
    enhanced_content.append("## Directory Summary\n\n")
    enhanced_content.append(f"This directory contains {len(files)} files and {len(subdirs)} subdirectories.\n\n")
    
    # Add file type statistics
    if files:
        extension_counts = {}
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext:
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        if extension_counts:
            enhanced_content.append("### File Types\n\n")
            for ext, count in sorted(extension_counts.items(), key=lambda x: x[1], reverse=True):
                enhanced_content.append(f"* {ext}: {count} files\n")
    
    # Write enhanced README.md
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(''.join(enhanced_content))
    
    print(f"Enhanced README.md for {directory}")

def enhance_python_docstrings(file_path: str) -> None:
"""Enhance docstrings in a Python file to follow Google style.
    
Args::
        file_path: Path to the Python file"""
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Parse the Python file
        tree = ast.parse(content)
        
        # Track positions of docstrings to modify
        modifications = []
        
        # Check module docstring
        module_docstring = ast.get_docstring(tree)
        if module_docstring:
            # Enhance module docstring
            enhanced_docstring = enhance_docstring(module_docstring)
            if enhanced_docstring != module_docstring:
                # Find position of module docstring
                for node in tree.body:
                    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                        start = node.lineno
                        end = node.end_lineno if hasattr(node, 'end_lineno') else start
                        modifications.append((start, end, enhanced_docstring))
                        break
        
        # Check class and function docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                docstring = ast.get_docstring(node)
                if docstring:
                    # Enhance docstring
                    enhanced_docstring = enhance_docstring(docstring)
                    if enhanced_docstring != docstring:
                        # Find position of docstring
                        for child in node.body:
                            if isinstance(child, ast.Expr) and isinstance(child.value, ast.Str):
                                start = child.lineno
                                end = child.end_lineno if hasattr(child, 'end_lineno') else start
                                modifications.append((start, end, enhanced_docstring))
                                break
        
        # Apply modifications in reverse order to avoid position shifts
        if modifications:
            lines = content.split('\n')
            for start, end, new_docstring in sorted(modifications, reverse=True):
                # Replace the docstring
                indent = re.match(r'^(\s*)', lines[start-1]).group(1)
                docstring_lines = [f'{indent}"""{new_docstring}"""']
                lines[start-1:end] = docstring_lines
            
            # Write modified content back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            print(f"Enhanced docstrings in {file_path}")
    
    except Exception as e:
        print(f"Error enhancing docstrings in {file_path}: {str(e)}")

def enhance_docstring(docstring: str) -> str:
"""Enhance a docstring to follow Google style.
    
Args::
        docstring: Original docstring
        
Returns::
        Enhanced docstring"""
    """
    # Remove leading/trailing whitespace
    docstring = docstring.strip()
    
    # Check if docstring is already in Google style
    if re.search(r'Args:', docstring) or re.search(r'Returns:', docstring):
        return docstring
    
    # Extract description
    description_lines = []
    param_lines = []
    return_lines = []
    
    # Simple parsing of existing docstring
    current_section = 'description'
    for line in docstring.split('\n'):
        line = line.strip()
        
        if line.startswith(':param') or line.startswith('@param'):
            current_section = 'params'
            param_match = re.search(r':param\s+(\w+):\s*(.*)', line)
            if param_match:
                param_name = param_match.group(1)
                param_desc = param_match.group(2)
                param_lines.append(f"    {param_name}: {param_desc}")
        elif line.startswith(':return') or line.startswith('@return'):
            current_section = 'returns'
            return_match = re.search(r':return.*?:\s*(.*)', line)
            if return_match:
                return_desc = return_match.group(1)
                return_lines.append(f"    {return_desc}")
        elif current_section == 'description' and line:
            description_lines.append(line)
    
    # Build enhanced docstring
    enhanced_lines = []
    
    # Add description
    if description_lines:
        enhanced_lines.extend(description_lines)
        enhanced_lines.append("")
    
    # Add Args section
    if param_lines:
        enhanced_lines.append("Args:")
        enhanced_lines.extend(param_lines)
        enhanced_lines.append("")
    
    # Add Returns section
    if return_lines:
        enhanced_lines.append("Returns:")
        enhanced_lines.extend(return_lines)
    
    return '\n'.join(enhanced_lines).strip()

def process_directory(directory: str) -> None:
"""Process a directory to enhance documentation.
    
Args::
        directory: Path to the directory"""
    """
    # Skip excluded directories
    if os.path.basename(directory) in EXCLUDE_DIRS:
        return
    
    print(f"Processing {directory}...")
    
    # Enhance README.md
    enhance_readme(directory)
    
    # Enhance Python docstrings
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        
        if os.path.isfile(item_path) and item.endswith('.py'):
            enhance_python_docstrings(item_path)
        elif os.path.isdir(item_path) and item not in EXCLUDE_DIRS and not item.startswith('.'):
            process_directory(item_path)

def create_missing_readme(directory: str) -> None:
"""Create README.md for directories that don't have one.
    
Args::
        directory: Path to the directory"""
    """
    readme_path = os.path.join(directory, "README.md")
    
    # Skip if README.md already exists
    if os.path.exists(readme_path):
        return
    
    # Get directory name
    dir_name = os.path.basename(directory)
    
    # Get parent directory
    parent_dir = os.path.dirname(directory)
    parent_name = os.path.basename(parent_dir)
    
    # Get all files in the directory
    files = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path) and item not in EXCLUDE_FILES and not item.startswith('.'):
            files.append(item)
    
    # Get all subdirectories
    subdirs = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path) and item not in EXCLUDE_DIRS and not item.startswith('.'):
            subdirs.append(item)
    
    # Create README content
    content = []
    
    # Add header
    content.append(f"# {dir_name}\n\n")
    
    # Add description
    if "data" in dir_name.lower():
        content.append("This directory contains data files used for backtesting and analysis.\n\n")
    else:
        content.append(f"This directory contains files related to {dir_name}.\n\n")
    
    # Add navigation section
    content.append("## Navigation\n\n")
    
    # Add link to root directory
    root_path = os.path.relpath('/workspace/backtrader', directory)
    content.append(f"* [🏠 Root Directory]({root_path}/README.md)\n")
    
    # Add link to parent directory
    if parent_dir and parent_dir != '/workspace/backtrader':
        content.append(f"* [⬆️ Parent Directory ({parent_name})]({os.path.relpath(parent_dir, directory)}/README.md)\n")
    
    # Add links to subdirectories
    if subdirs:
        content.append("\n### Subdirectories\n\n")
        for subdir in sorted(subdirs):
            content.append(f"* [{subdir}]({subdir}/README.md) - Directory containing {subdir} related files\n")
    
    # Add file documentation
    if files:
        content.append("\n## Files\n\n")
        
        for file in sorted(files):
            content.append(f"### {file}\n\n")
            
            if file.endswith('.py'):
                # Try to analyze Python file
                try:
                    with open(os.path.join(directory, file), 'r', encoding='utf-8', errors='replace') as f:
                        file_content = f.read()
                    
                    # Look for docstring
                    docstring_match = re.search(r'"""(.*?)"""', file_content, re.DOTALL)
                    if docstring_match:
                        docstring = docstring_match.group(1).strip()
                        first_line = docstring.split('\n')[0].strip()
                        content.append(f"{first_line}\n\n")
                    else:
                        content.append(f"Python file.\n\n")
                except:
                    content.append(f"Python file.\n\n")
            else:
                content.append(f"File with {os.path.splitext(file)[1]} extension.\n\n")
    
    # Add directory summary
    content.append("## Directory Summary\n\n")
    content.append(f"This directory contains {len(files)} files and {len(subdirs)} subdirectories.\n\n")
    
    # Add file type statistics
    if files:
        extension_counts = {}
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext:
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        if extension_counts:
            content.append("### File Types\n\n")
            for ext, count in sorted(extension_counts.items(), key=lambda x: x[1], reverse=True):
                content.append(f"* {ext}: {count} files\n")
    
    # Write README.md
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(''.join(content))
    
    print(f"Created README.md for {directory}")

def main():
    """Main function to enhance documentation for the entire repository."""
    # Start from the repository root
    repo_root = '/workspace/backtrader'
    
    # First, create README.md for directories that don't have one
    for root, dirs, files in os.walk(repo_root):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
        
        # Create README.md if it doesn't exist
        if "README.md" not in files:
            create_missing_readme(root)
    
    # Then, enhance existing README.md files
    process_directory(repo_root)
    
    print("Documentation enhancement completed!")

if __name__ == "__main__":
    main()