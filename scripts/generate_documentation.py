#!/usr/bin/env python3
"""Documentation Generator for Backtrader Repository
This script recursively traverses the repository directory structure and generates
README.md files for each directory, documenting the purpose and content of each file
and subdirectory. It also creates links between parent and child directories for
easy navigation.
Usage:
python generate_documentation.py
Author: OpenHands AI"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Directories to exclude from documentation
EXCLUDE_DIRS = {
    '.git', '__pycache__', '.github', 'venv', 'env', '.venv', '.env',
    'node_modules', 'dist', 'build', '.idea', '.vscode', '.pytest_cache',
    'scripts'  # Exclude the scripts directory itself
}

# Files to exclude from documentation
EXCLUDE_FILES = {
    '.gitignore', '.gitattributes', '.DS_Store', 'Thumbs.db', '.env',
    '.editorconfig', '.prettierrc', '.eslintrc', '.babelrc', '.dockerignore',
    'package-lock.json', 'yarn.lock', 'poetry.lock', 'Pipfile.lock'
}

# File extensions to document
INCLUDE_EXTENSIONS = {
    '.py', '.js', '.java', '.c', '.cpp', '.h', '.hpp', '.sh', '.md',
    '.txt', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.html', '.css', '.scss', '.less', '.sql', '.r', '.rb', '.go', '.rs',
    '.ts', '.tsx', '.jsx', '.php', '.pl', '.pm', '.kt', '.kts', '.swift',
    '.m', '.mm', '.f', '.f90', '.f95', '.f03', '.f08', '.lua', '.tcl',
    '.groovy', '.scala', '.clj', '.cs', '.fs', '.ml', '.mli', '.hs', '.lhs',
    '.erl', '.ex', '.exs', '.elm', '.dart', '.d', '.jl', '.v', '.vhd', '.vhdl'
}

def detect_non_english(text: str) -> bool:
"""Detect if text contains non-English content (focusing on Portuguese, German, Chinese).
    
Args::
        text: Text to analyze
        
Returns::
        True if non-English content is detected, False otherwise"""
    """
    # Common Portuguese words and patterns
    portuguese_patterns = [
        r'\bfaça\b', r'\bestá\b', r'\bfunção\b', r'\bvariáveis\b', r'\bpara o\b',
        r'\bcomo um\b', r'\bnão é\b', r'\butilitários\b', r'\bnotificação\b',
        r'\badicione\b', r'\bexemplo\b', r'\biniciando\b', r'\btestando\b'
    ]
    
    # Common German words and patterns
    german_patterns = [
        r'\bwenn\b', r'\bhier\b', r'\bwird\b', r'\bnoch\b', r'\bbereits\b',
        r'\bganz\b', r'\bblöde\b', r'\bidee\b', r'\bformulierung\b', r'\bäquivalent\b',
        r'\bmarkt\b', r'\bdaten\b', r'\bwerte\b', r'\bberechnung\b', r'\bbeispiel\b',
        r'\bausgabe\b', r'\berstelle\b', r'\bkauf\b', r'\bverkauf\b', r'\bverfolge\b',
        r'\bbestellung\b'
    ]
    
    # Check for Chinese characters
    chinese_pattern = r'[\u4e00-\u9fff]'
    
    # Check for Portuguese patterns
    for pattern in portuguese_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check for German patterns
    for pattern in german_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check for Chinese characters
    if re.search(chinese_pattern, text):
        return True
    
    return False

def translate_comment(comment: str) -> str:
"""Translate common non-English comments to English.
    
Args::
        comment: Comment to translate
        
Returns::
        Translated comment"""
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
    
    # Chinese translations would be more complex, but we'll handle basic detection
    
    # Apply translations
    translated = comment
    
    # Portuguese translations
    for pt, en in pt_to_en.items():
        translated = re.sub(r'\b' + pt + r'\b', en, translated, flags=re.IGNORECASE)
    
    # German translations
    for de, en in de_to_en.items():
        translated = re.sub(r'\b' + de + r'\b', en, translated, flags=re.IGNORECASE)
    
    # If Chinese characters are detected, add a note
    if re.search(r'[\u4e00-\u9fff]', comment):
        translated += " [Contains Chinese characters that should be translated]"
    
    return translated

def get_file_description(file_path: str) -> str:
"""Analyze a file and return a description of its purpose.
    
Args::
        file_path: Path to the file to analyze
        
Returns::
        A string describing the file's purpose"""
    """
    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_name)[1].lower()
    
    # Skip binary files and very large files
    if ext not in INCLUDE_EXTENSIONS:
        return f"Binary or data file"
    
    try:
        file_size = os.path.getsize(file_path)
        if file_size > 1_000_000:  # Skip files larger than 1MB
            return f"Large file ({file_size / 1_000_000:.1f} MB)"
            
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(10000)  # Read first 10KB to analyze
        
        # Check for non-English content
        has_non_english = detect_non_english(content)
        
        # Extract docstring or file header comment
        if ext == '.py':
            # Look for module docstring
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if docstring_match:
                docstring = docstring_match.group(1).strip()
                first_line = docstring.split('\n')[0].strip()
                
                # Translate if non-English
                if has_non_english:
                    first_line = translate_comment(first_line)
                
                return first_line
            
            # Look for class definitions with docstrings
            class_matches = re.finditer(r'class\s+(\w+).*?:.*?"""(.*?)"""', content, re.DOTALL)
            for match in class_matches:
                class_name = match.group(1)
                class_doc = match.group(2).strip().split('\n')[0].strip()
                
                # Translate if non-English
                if has_non_english:
                    class_doc = translate_comment(class_doc)
                
                return f"Defines the {class_name} class: {class_doc}"
            
            # Look for function definitions with docstrings
            func_matches = re.finditer(r'def\s+(\w+).*?:.*?"""(.*?)"""', content, re.DOTALL)
            for match in func_matches:
                func_name = match.group(1)
                func_doc = match.group(2).strip().split('\n')[0].strip()
                
                # Translate if non-English
                if has_non_english:
                    func_doc = translate_comment(func_doc)
                
                return f"Defines the {func_name} function: {func_doc}"
            
            # Look for simple class or function definitions
            class_match = re.search(r'class\s+(\w+)', content)
            if class_match:
                return f"Defines the {class_match.group(1)} class"
                
            func_match = re.search(r'def\s+(\w+)', content)
            if func_match:
                return f"Defines the {func_match.group(1)} function"
        
        # For other file types, try to infer purpose from content and name
        if 'test' in file_name.lower():
            return "Test file"
        elif 'config' in file_name.lower() or ext in {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf'}:
            return "Configuration file"
        elif ext in {'.md', '.txt'}:
            return "Documentation file"
        elif 'setup' in file_name.lower():
            return "Setup/installation file"
        elif 'requirements' in file_name.lower():
            return "Dependencies specification file"
        
        # Add warning about non-English content
        non_english_warning = " (Contains non-English content that should be translated)" if has_non_english else ""
        
        # Default description based on file type
        if ext == '.py':
            return f"Python module{non_english_warning}"
        elif ext == '.js':
            return f"JavaScript module{non_english_warning}"
        elif ext == '.java':
            return f"Java source file{non_english_warning}"
        elif ext == '.c' or ext == '.cpp':
            return f"C/C++ source file{non_english_warning}"
        elif ext == '.h' or ext == '.hpp':
            return f"C/C++ header file{non_english_warning}"
        elif ext == '.sh':
            return f"Shell script{non_english_warning}"
        else:
            return f"File with {ext} extension{non_english_warning}"
            
    except Exception as e:
        return f"Could not analyze file: {str(e)}"

def get_directory_description(directory: str) -> str:
"""Generate a description for a directory based on its name and contents.
    
Args::
        directory: Path to the directory
        
Returns::
        A string describing the directory's purpose"""
    """
    dir_name = os.path.basename(directory)
    
    # Common directory name patterns and their descriptions
    dir_patterns = {
        'test': 'Contains test files and test utilities',
        'tests': 'Contains test files and test utilities',
        'doc': 'Contains documentation',
        'docs': 'Contains documentation',
        'example': 'Contains example code and usage demonstrations',
        'examples': 'Contains example code and usage demonstrations',
        'src': 'Contains source code',
        'lib': 'Contains library code',
        'utils': 'Contains utility functions and helper code',
        'util': 'Contains utility functions and helper code',
        'scripts': 'Contains scripts for various tasks',
        'config': 'Contains configuration files',
        'data': 'Contains data files',
        'resources': 'Contains resource files',
        'assets': 'Contains asset files',
        'images': 'Contains image files',
        'img': 'Contains image files',
        'css': 'Contains CSS stylesheets',
        'js': 'Contains JavaScript files',
        'templates': 'Contains template files',
        'model': 'Contains model definitions',
        'models': 'Contains model definitions',
        'view': 'Contains view components',
        'views': 'Contains view components',
        'controller': 'Contains controller logic',
        'controllers': 'Contains controller logic',
        'api': 'Contains API-related code',
        'services': 'Contains service implementations',
        'service': 'Contains service implementations',
        'middleware': 'Contains middleware components',
        'migrations': 'Contains database migration files',
        'fixtures': 'Contains test fixtures or sample data',
        'static': 'Contains static files',
        'public': 'Contains publicly accessible files',
        'private': 'Contains private or sensitive files',
        'vendor': 'Contains third-party dependencies',
        'node_modules': 'Contains Node.js dependencies',
        'bin': 'Contains executable files',
        'tools': 'Contains tools and utilities',
        'contrib': 'Contains contributed code',
        'plugins': 'Contains plugin modules',
        'extensions': 'Contains extension modules',
        'core': 'Contains core functionality',
        'common': 'Contains common code shared across the project',
        'shared': 'Contains shared resources or code',
        'helpers': 'Contains helper functions',
        'hooks': 'Contains hook implementations',
        'interfaces': 'Contains interface definitions',
        'types': 'Contains type definitions',
        'constants': 'Contains constant definitions',
        'enums': 'Contains enumeration definitions',
        'exceptions': 'Contains exception definitions',
        'errors': 'Contains error definitions',
        'logging': 'Contains logging-related code',
        'cache': 'Contains caching-related code',
        'storage': 'Contains storage-related code',
        'database': 'Contains database-related code',
        'db': 'Contains database-related code',
        'auth': 'Contains authentication-related code',
        'security': 'Contains security-related code',
        'i18n': 'Contains internationalization code',
        'locales': 'Contains localization files',
        'translations': 'Contains translation files',
        'backup': 'Contains backup files',
        'temp': 'Contains temporary files',
        'tmp': 'Contains temporary files',
        'logs': 'Contains log files',
        'log': 'Contains log files',
        'build': 'Contains build artifacts',
        'dist': 'Contains distribution files',
        'release': 'Contains release files',
        'deploy': 'Contains deployment scripts or configurations',
        'ci': 'Contains continuous integration configurations',
        'cd': 'Contains continuous deployment configurations',
        'docker': 'Contains Docker-related files',
        'kubernetes': 'Contains Kubernetes configurations',
        'k8s': 'Contains Kubernetes configurations',
        'helm': 'Contains Helm charts',
        'terraform': 'Contains Terraform configurations',
        'ansible': 'Contains Ansible playbooks',
        'vagrant': 'Contains Vagrant configurations',
        'aws': 'Contains AWS-related code or configurations',
        'azure': 'Contains Azure-related code or configurations',
        'gcp': 'Contains Google Cloud Platform-related code or configurations',
        'strategies': 'Contains trading strategy implementations',
        'indicators': 'Contains technical indicator implementations',
        'analyzers': 'Contains analysis tools and metrics',
        'feeds': 'Contains data feed implementations',
        'brokers': 'Contains broker implementations',
        'observers': 'Contains observer implementations',
        'sizers': 'Contains position sizing implementations',
        'filters': 'Contains data filtering implementations',
        'stores': 'Contains store implementations',
        'commissions': 'Contains commission models',
        'plot': 'Contains plotting functionality',
        'arbitrage': 'Contains arbitrage strategy implementations',
        'backtest': 'Contains backtesting functionality',
        'live': 'Contains live trading functionality',
        'sandbox': 'Contains experimental or sandbox code',
        'contrib': 'Contains contributed code',
        'samples': 'Contains sample code and examples',
        'tutorials': 'Contains tutorial code and examples'
    }
    
    # Check for directory name matches
    for pattern, description in dir_patterns.items():
        if dir_name.lower() == pattern.lower():
            return description
    
    # If no direct match, try partial matches
    for pattern, description in dir_patterns.items():
        if pattern.lower() in dir_name.lower():
            return description
    
    # Default description
    return f"Directory containing {dir_name} related files"

def analyze_directory_context(directory: str, files: list) -> str:
"""Analyze the context of a directory based on its files.
    
Args::
        directory: Path to the directory
        files: List of files in the directory
        
Returns::
        A string describing the directory's context"""
    """
    # Count file extensions to determine the primary purpose
    extension_counts = {}
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext:
            extension_counts[ext] = extension_counts.get(ext, 0) + 1
    
    # Sort extensions by count
    sorted_extensions = sorted(extension_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Determine primary language/technology
    primary_tech = None
    if sorted_extensions:
        primary_ext = sorted_extensions[0][0]
        if primary_ext == '.py':
            primary_tech = 'Python'
        elif primary_ext == '.js':
            primary_tech = 'JavaScript'
        elif primary_ext == '.java':
            primary_tech = 'Java'
        elif primary_ext == '.c' or primary_ext == '.cpp' or primary_ext == '.h' or primary_ext == '.hpp':
            primary_tech = 'C/C++'
        elif primary_ext == '.rb':
            primary_tech = 'Ruby'
        elif primary_ext == '.go':
            primary_tech = 'Go'
        elif primary_ext == '.rs':
            primary_tech = 'Rust'
        elif primary_ext == '.php':
            primary_tech = 'PHP'
        elif primary_ext == '.cs':
            primary_tech = 'C#'
        elif primary_ext == '.ts':
            primary_tech = 'TypeScript'
        elif primary_ext == '.html' or primary_ext == '.css':
            primary_tech = 'Web'
        elif primary_ext == '.md' or primary_ext == '.txt':
            primary_tech = 'Documentation'
        elif primary_ext == '.json' or primary_ext == '.yaml' or primary_ext == '.yml':
            primary_tech = 'Configuration'
        elif primary_ext == '.sh':
            primary_tech = 'Shell'
        else:
            primary_tech = f'{primary_ext} files'
    
    # Check for specific file patterns
    has_tests = any('test' in file.lower() for file in files)
    has_examples = any('example' in file.lower() for file in files)
    has_docs = any(file.lower().endswith(('.md', '.txt', '.rst', '.adoc')) for file in files)
    has_config = any(file.lower().endswith(('.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf')) for file in files)
    
    # Build context description
    context_parts = []
    
    if primary_tech:
        context_parts.append(f"Primarily contains {primary_tech} code")
    
    if has_tests:
        context_parts.append("includes test files")
    
    if has_examples:
        context_parts.append("includes example code")
    
    if has_docs:
        context_parts.append("includes documentation")
    
    if has_config:
        context_parts.append("includes configuration files")
    
    # Join parts with appropriate conjunctions
    if len(context_parts) == 1:
        return context_parts[0]
    elif len(context_parts) == 2:
        return f"{context_parts[0]} and {context_parts[1]}"
    elif len(context_parts) > 2:
        return f"{', '.join(context_parts[:-1])}, and {context_parts[-1]}"
    else:
        return "Contains various files"

def generate_readme(directory: str, parent_dir: str = None) -> None:
"""Generate a README.md file for the specified directory.
    
Args::
        directory: Path to the directory to document
        parent_dir: Path to the parent directory (for creating links)"""
    """
    dir_path = Path(directory)
    dir_name = dir_path.name
    
    # Skip excluded directories
    if dir_name in EXCLUDE_DIRS:
        return
    
    # Get all subdirectories and files
    subdirs = []
    files = []
    
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        
        if os.path.isdir(item_path):
            if item not in EXCLUDE_DIRS and not item.startswith('.'):
                subdirs.append(item)
        elif os.path.isfile(item_path):
            if item not in EXCLUDE_FILES and not item.startswith('.'):
                files.append(item)
    
    # Sort subdirectories and files alphabetically
    subdirs.sort()
    files.sort()
    
    # Get directory description and context
    dir_description = get_directory_description(directory)
    dir_context = analyze_directory_context(directory, files)
    
    # Create README.md content
    content = [f"# {dir_name}\n\n"]
    content.append(f"{dir_description}. {dir_context}.\n\n")
    
    # Add navigation links
    content.append("## Navigation\n\n")
    
    if parent_dir:
        parent_name = os.path.basename(parent_dir)
        content.append(f"* [↑ Parent Directory ({parent_name})](../README.md)\n")
    else:
        # This is the root directory
        content.append("* This is the root directory of the repository\n")
    
    if subdirs:
        content.append("\n### Subdirectories\n\n")
        for subdir in subdirs:
            # Get a brief description for the subdirectory
            subdir_path = os.path.join(directory, subdir)
            subdir_desc = get_directory_description(subdir_path)
            content.append(f"* [{subdir}]({subdir}/README.md) - {subdir_desc}\n")
    
    # Add files section
    if files:
        content.append("\n## Files\n\n")
        for file in files:
            if file == "README.md":
                continue
                
            file_path = os.path.join(directory, file)
            description = get_file_description(file_path)
            content.append(f"### {file}\n\n")
            content.append(f"{description}\n\n")
    
    # Add a summary section
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
    
    # Write README.md file
    readme_path = os.path.join(directory, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(''.join(content))
    
    print(f"Generated README.md for {directory}")
    
    # Recursively generate README.md for subdirectories
    for subdir in subdirs:
        subdir_path = os.path.join(directory, subdir)
        generate_readme(subdir_path, directory)

def main():
    """Main function to generate documentation for the entire repository."""
    # Start from the repository root
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"Generating documentation for repository: {repo_root}")
    generate_readme(repo_root)
    print("Documentation generation complete!")

if __name__ == "__main__":
    main()