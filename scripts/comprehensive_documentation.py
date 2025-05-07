#!/usr/bin/env python3
"""Comprehensive Documentation Generator for Backtrader Repository

This script creates comprehensive documentation for the Backtrader repository,
including detailed README.md files for each directory and improved docstrings
for Python files.

Usage:
    python comprehensive_documentation.py

Author: OpenHands AI"""
"""

import os
import re
import sys
import ast
import inspect
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import textwrap

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

# Directory descriptions
DIR_DESCRIPTIONS = {
    'backtrader': 'Core module of the Backtrader framework, containing the main components for backtesting trading strategies',
    'analyzers': 'Modules for analyzing trading strategy performance, including metrics like Sharpe ratio, drawdown, and returns',
    'brokers': 'Broker implementations for simulating trading environments, handling orders, and managing positions',
    'commissions': 'Commission models for simulating various fee structures in trading',
    'feeds': 'Data feed implementations for loading market data from various sources',
    'filters': 'Data filtering implementations for preprocessing market data',
    'indicators': 'Technical indicators for market analysis, such as moving averages, oscillators, and volatility measures',
    'observers': 'Observer implementations for tracking and visualizing strategy performance',
    'sizers': 'Position sizing implementations for determining trade sizes',
    'stores': 'Store implementations for connecting to data providers and brokers',
    'strategies': 'Trading strategy implementations and base classes',
    'utils': 'Utility functions and helper code for the Backtrader framework',
    'samples': 'Sample code and examples demonstrating Backtrader usage',
    'tests': 'Test files and utilities for ensuring Backtrader functionality',
    'docs': 'Documentation files for the Backtrader framework',
    'contrib': 'Contributed code from the Backtrader community',
    'tools': 'Tools and utilities for working with Backtrader',
    'scripts': 'Scripts for various tasks related to Backtrader',
    'data': 'Data files for backtesting',
    'datas': 'Data files for backtesting',
    'arbitrage': 'Arbitrage strategy implementations for exploiting price differences',
    'backtest': 'Backtesting functionality and utilities',
    'turtle': 'Turtle trading system implementation',
    'xtquant': 'Integration with xtquant trading platform',
    'qmtbt': 'Integration with QMT trading platform',
    'signals': 'Signal generation for trading strategies',
    'studies': 'Market studies and analysis tools',
    'plot': 'Plotting functionality for visualizing trading results',
    'orders': 'Order handling and management',
    'listeners': 'Event listeners for tracking trading activity',
    'engine': 'Core engine components for running backtests',
    'btrun': 'Command-line interface for running Backtrader',
    'metatable': 'Metadata handling utilities',
    'config': 'Configuration files and utilities',
    'doc': 'Documentation files',
    'logs': 'Log files and logging utilities',
    'outcome': 'Output and results from backtests',
    'prompts': 'Prompt templates and utilities',
    'reference': 'Reference materials and documentation',
    'sandbox': 'Experimental or sandbox code',
    'src': 'Source code for additional components',
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

def get_directory_description(directory: str) -> str:
"""Get a description for a directory based on its name.
    
Args::
        directory: Path to the directory
        
Returns::
        A string describing the directory's purpose"""
    """
    dir_name = os.path.basename(directory)
    
    # Check if we have a predefined description
    for key, description in DIR_DESCRIPTIONS.items():
        if dir_name.lower() == key.lower():
            return description
    
    # If no direct match, try partial matches
    for key, description in DIR_DESCRIPTIONS.items():
        if key.lower() in dir_name.lower():
            return description
    
    # Default description
    return f"Directory containing {dir_name} related files"

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
            
            elif isinstance(node, ast.FunctionDef):
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

def get_file_description(file_path: str) -> str:
"""Get a description for a file based on its content.
    
Args::
        file_path: Path to the file
        
Returns::
        A string describing the file's purpose"""
    """
    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_name)[1].lower()
    
    # Skip binary files and very large files
    if ext not in ['.py', '.md', '.txt', '.rst', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.sh']:
        return f"Binary or data file"
    
    try:
        file_size = os.path.getsize(file_path)
        if file_size > 1_000_000:  # Skip files larger than 1MB
            return f"Large file ({file_size / 1_000_000:.1f} MB)"
            
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(10000)  # Read first 10KB to analyze
        
        # For Python files, extract docstring
        if ext == '.py':
            # Look for module docstring
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if docstring_match:
                docstring = docstring_match.group(1).strip()
                first_line = docstring.split('\n')[0].strip()
                
                # Translate if non-English
                if re.search(r'[\u4e00-\u9fff]', first_line) or any(word in first_line.lower() for word in ['faça', 'está', 'função', 'variáveis', 'wenn', 'hier', 'wird']):
                    first_line = translate_to_english(first_line)
                
                return first_line
            
            # Look for class definitions with docstrings
            class_matches = re.finditer(r'class\s+(\w+).*?:.*?"""(.*?)"""', content, re.DOTALL)
            for match in class_matches:
                class_name = match.group(1)
                class_doc = match.group(2).strip().split('\n')[0].strip()
                
                # Translate if non-English
                if re.search(r'[\u4e00-\u9fff]', class_doc) or any(word in class_doc.lower() for word in ['faça', 'está', 'função', 'variáveis', 'wenn', 'hier', 'wird']):
                    class_doc = translate_to_english(class_doc)
                
                return f"Defines the {class_name} class: {class_doc}"
            
            # Look for function definitions with docstrings
            func_matches = re.finditer(r'def\s+(\w+).*?:.*?"""(.*?)"""', content, re.DOTALL)
            for match in func_matches:
                func_name = match.group(1)
                func_doc = match.group(2).strip().split('\n')[0].strip()
                
                # Translate if non-English
                if re.search(r'[\u4e00-\u9fff]', func_doc) or any(word in func_doc.lower() for word in ['faça', 'está', 'função', 'variáveis', 'wenn', 'hier', 'wird']):
                    func_doc = translate_to_english(func_doc)
                
                return f"Defines the {func_name} function: {func_doc}"
        
        # For other file types, try to infer purpose from content and name
        if 'test' in file_name.lower():
            return "Test file for verifying functionality"
        elif 'config' in file_name.lower() or ext in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf']:
            return "Configuration file for setting parameters and options"
        elif ext in ['.md', '.txt', '.rst']:
            return "Documentation file providing information and guidance"
        elif 'setup' in file_name.lower():
            return "Setup/installation file for configuring the environment"
        elif 'requirements' in file_name.lower():
            return "Dependencies specification file listing required packages"
        
        # Default description based on file type
        if ext == '.py':
            return "Python module for implementing functionality"
        elif ext == '.sh':
            return "Shell script for automating tasks"
        else:
            return f"File with {ext} extension"
            
    except Exception as e:
        return f"Could not analyze file: {str(e)}"

def create_comprehensive_readme(directory: str) -> None:
"""Create a comprehensive README.md file for a directory.
    
Args::
        directory: Path to the directory"""
    """
    readme_path = os.path.join(directory, "README.md")
    
    # Get directory name and description
    dir_name = os.path.basename(directory)
    dir_description = get_directory_description(directory)
    
    # Get all files and subdirectories
    files = []
    subdirs = []
    
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        
        if os.path.isfile(item_path) and item not in EXCLUDE_FILES and not item.startswith('.'):
            files.append(item)
        elif os.path.isdir(item_path) and item not in EXCLUDE_DIRS and not item.startswith('.'):
            subdirs.append(item)
    
    # Sort files and subdirectories
    files.sort()
    subdirs.sort()
    
    # Create README content
    content = []
    
    # Add header and description
    content.append(f"# {dir_name}\n\n")
    content.append(f"{dir_description}.\n\n")
    
    # Add navigation section
    content.append("## Navigation\n\n")
    
    # Add link to root directory
    root_path = os.path.relpath('/workspace/backtrader', directory)
    content.append(f"* [🏠 Root Directory]({root_path}/README.md)\n")
    
    # Add link to parent directory
    parent_dir = os.path.dirname(directory)
    if parent_dir and parent_dir != '/workspace/backtrader':
        parent_name = os.path.basename(parent_dir)
        content.append(f"* [⬆️ Parent Directory ({parent_name})]({os.path.relpath(parent_dir, directory)}/README.md)\n")
    
    # Add table of contents
    content.append("\n## Table of Contents\n\n")
    content.append("* [Subdirectories](#subdirectories)\n")
    content.append("* [Files](#files)\n")
    content.append("* [Directory Summary](#directory-summary)\n")
    
    # Add subdirectories section
    if subdirs:
        content.append("\n## Subdirectories\n\n")
        
        for subdir in subdirs:
            subdir_path = os.path.join(directory, subdir)
            subdir_description = get_directory_description(subdir_path)
            
            content.append(f"### [{subdir}]({subdir}/README.md)\n\n")
            content.append(f"{subdir_description}.\n\n")
    
    # Add files section
    if files:
        content.append("\n## Files\n\n")
        
        for file in files:
            if file == "README.md":
                continue
                
            file_path = os.path.join(directory, file)
            file_description = get_file_description(file_path)
            
            content.append(f"### {file}\n\n")
            content.append(f"{file_description}.\n\n")
            
            # For Python files, add more detailed information
            if file.endswith('.py'):
                file_info = analyze_python_file(file_path)
                
                # Add classes
                classes = file_info.get('classes', [])
                if classes:
                    content.append("**Classes:**\n\n")
                    
                    for cls in classes:
                        cls_name = cls.get('name', '')
                        cls_docstring = cls.get('docstring', '')
                        
                        if cls_docstring:
                            # Format docstring
                            cls_docstring = cls_docstring.split('\n\n')[0].strip()
                            content.append(f"* `{cls_name}`: {cls_docstring}\n")
                        else:
                            content.append(f"* `{cls_name}`\n")
                    
                    content.append("\n")
                
                # Add functions
                functions = file_info.get('functions', [])
                if functions:
                    content.append("**Functions:**\n\n")
                    
                    for func in functions:
                        func_name = func.get('name', '')
                        func_docstring = func.get('docstring', '')
                        
                        if func_docstring:
                            # Format docstring
                            func_docstring = func_docstring.split('\n\n')[0].strip()
                            content.append(f"* `{func_name}`: {func_docstring}\n")
                        else:
                            content.append(f"* `{func_name}`\n")
                    
                    content.append("\n")
    
    # Add directory summary
    content.append("\n## Directory Summary\n\n")
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
    
    print(f"Created comprehensive README.md for {directory}")

def enhance_python_docstrings(file_path: str) -> None:
"""Enhance docstrings in a Python file to follow Google style.
    
Args::
        file_path: Path to the Python file"""
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Check if file has non-English content
        has_non_english = re.search(r'[\u4e00-\u9fff]', content) or any(word in content.lower() for word in ['faça', 'está', 'função', 'variáveis', 'wenn', 'hier', 'wird'])
        
        # Parse the Python file
        tree = ast.parse(content)
        
        # Track positions of docstrings to modify
        modifications = []
        
        # Check module docstring
        module_docstring = ast.get_docstring(tree)
        if module_docstring:
            # Enhance module docstring
            enhanced_docstring = enhance_docstring(module_docstring, has_non_english)
            if enhanced_docstring != module_docstring:
                # Find position of module docstring
                for node in tree.body:
                    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
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
                    enhanced_docstring = enhance_docstring(docstring, has_non_english)
                    if enhanced_docstring != docstring:
                        # Find position of docstring
                        for child in node.body:
                            if isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant) and isinstance(child.value.value, str):
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

def enhance_docstring(docstring: str, translate: bool = False) -> str:
"""Enhance a docstring to follow Google style.
    
Args::
        docstring: Original docstring
        translate: Whether to translate non-English content
        
Returns::
        Enhanced docstring"""
    """
    # Remove leading/trailing whitespace
    docstring = docstring.strip()
    
    # Translate if needed
    if translate:
        docstring = translate_to_english(docstring)
    
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
    
    # Create comprehensive README.md
    create_comprehensive_readme(directory)
    
    # Process files
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        
        if os.path.isfile(item_path) and item.endswith('.py'):
            enhance_python_docstrings(item_path)
        elif os.path.isdir(item_path) and item not in EXCLUDE_DIRS and not item.startswith('.'):
            process_directory(item_path)

def main():
    """Main function to enhance documentation for the entire repository."""
    # Start from the repository root
    repo_root = '/workspace/backtrader'
    
    # Process the repository
    process_directory(repo_root)
    
    print("Documentation enhancement completed!")

if __name__ == "__main__":
    main()