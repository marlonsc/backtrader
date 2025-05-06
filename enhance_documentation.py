#!/usr/bin/env python3
"""Documentation Enhancement Script

This script performs three main tasks:
1. Updates all README.md files with comprehensive documentation
2. Enhances docstrings in Python files to follow Google style guide
3. Translates non-English content to English where appropriate

The script recursively traverses the repository and processes all relevant files."""
"""

import os
import re
import sys
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union

# Directories to exclude from processing
EXCLUDE_DIRS = {'.git', '.github', '.vscode', '.cursor', '.devcontainer', '__pycache__'}

# File extensions that are considered source code
SOURCE_CODE_EXTENSIONS = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.java': 'Java',
    '.c': 'C',
    '.cpp': 'C++',
    '.h': 'C/C++ Header',
    '.hpp': 'C++ Header',
    '.sh': 'Shell',
    '.rb': 'Ruby',
    '.go': 'Go',
    '.rs': 'Rust',
    '.php': 'PHP',
    '.ts': 'TypeScript',
    '.lua': 'Lua',
    '.r': 'R',
    '.scala': 'Scala',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.cs': 'C#',
    '.fs': 'F#',
    '.hs': 'Haskell',
    '.pl': 'Perl',
    '.sql': 'SQL',
}

# Binary file extensions
BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',  # Images
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',  # Documents
    '.zip', '.tar', '.gz', '.rar', '.7z',  # Archives
    '.exe', '.dll', '.so', '.dylib',  # Executables and libraries
    '.pyc', '.pyo', '.pyd',  # Python compiled files
    '.class',  # Java compiled files
    '.o',  # Object files
}

# Configuration files
CONFIG_EXTENSIONS = {
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.xml', '.properties', '.env', '.gitignore', '.dockerignore',
}

def get_file_type(file_path: str) -> str:
"""Determine the type of a file based on its extension and content.
    
Args::
        file_path: Path to the file
        
Returns::
        A string describing the file type"""
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in SOURCE_CODE_EXTENSIONS:
        return f"{SOURCE_CODE_EXTENSIONS[ext]} source file"
    elif ext in BINARY_EXTENSIONS:
        return "Binary file"
    elif ext in CONFIG_EXTENSIONS:
        return "Configuration file"
    elif ext == '.md':
        return "Markdown documentation"
    elif ext == '.rst':
        return "reStructuredText documentation"
    elif ext == '.txt':
        return "Text file"
    elif ext == '.ipynb':
        return "Jupyter notebook"
    elif ext == '.csv':
        return "CSV data file"
    elif ext == '.html':
        return "HTML file"
    elif ext == '.css':
        return "CSS file"
    elif ext == '.js':
        return "JavaScript file"
    
    # Try to determine if it's a text file by reading a small portion
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return "Text file"
    except UnicodeDecodeError:
        return "Binary file"
    except Exception:
        return "Unknown file type"

def get_file_description(file_path: str) -> str:
"""Generate a description for a file based on its content.
    
Args::
        file_path: Path to the file
        
Returns::
        A string describing the file's purpose"""
    """
    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    
    # Skip binary files
    if ext in BINARY_EXTENSIONS:
        return f"Binary file ({ext[1:]} format)"
    
    # For source code files, try to extract docstring or comments
    if ext in SOURCE_CODE_EXTENSIONS:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(4096)  # Read first 4KB
                
                # For Python files, extract docstring
                if ext == '.py':
                    # Look for module docstring
                    module_docstring = re.search(r'"""(.*?)"""', content, re.DOTALL)
                    if module_docstring:
                        doc = module_docstring.group(1).strip()
                        # Return first line or first sentence if it's not too long
                        first_line = doc.split('\n')[0].strip()
                        if len(first_line) > 10 and len(first_line) < 100:
                            return first_line
                        
                        first_sentence = re.split(r'\.(?:\s|$)', doc)[0].strip()
                        if len(first_sentence) > 10 and len(first_sentence) < 100:
                            return first_sentence
                
                # For other files, look for comments at the beginning
                first_lines = content.split('\n')[:10]
                for line in first_lines:
                    # Look for common comment patterns
                    comment_match = re.search(r'[#/]{1,2}\s*(.*)', line)
                    if comment_match and len(comment_match.group(1).strip()) > 10:
                        return comment_match.group(1).strip()
        except Exception:
            pass
    
    # Default descriptions based on filename patterns
    if file_name == 'README.md':
        return "Documentation file with information about this directory"
    elif file_name == '__init__.py':
        return "Python package initialization file"
    elif file_name == 'setup.py':
        return "Python package setup file"
    elif file_name == 'requirements.txt':
        return "Python dependencies file"
    elif file_name.startswith('test_') and ext == '.py':
        return f"Test file for {file_name[5:]}"
    elif file_name == '.gitignore':
        return "Git ignore rules file"
    elif file_name == 'Dockerfile':
        return "Docker configuration file"
    elif file_name == 'docker-compose.yml' or file_name == 'docker-compose.yaml':
        return "Docker Compose configuration file"
    elif file_name == 'Makefile':
        return "Make build configuration file"
    elif file_name == 'LICENSE':
        return "License file"
    elif file_name == 'CHANGELOG.md' or file_name == 'changelog.txt':
        return "Change log file"
    elif file_name == 'pyproject.toml':
        return "Python project configuration file"
    elif file_name == 'tox.ini':
        return "Tox configuration file for Python testing"
    
    # Default to file type
    return get_file_type(file_path)

def get_directory_description(dir_path: str) -> str:
"""Generate a description for a directory based on its name and content.
    
Args::
        dir_path: Path to the directory
        
Returns::
        A string describing the directory's purpose"""
    """
    dir_name = os.path.basename(dir_path)
    
    # Check if there's an existing README.md with a description
    readme_path = os.path.join(dir_path, 'README.md')
    if os.path.exists(readme_path):
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for the first paragraph after the title
                match = re.search(r'#.*?\n+([^#\n].*?)(\n\n|\n#|$)', content, re.DOTALL)
                if match:
                    desc = match.group(1).strip()
                    if len(desc) > 10:  # Ensure it's a meaningful description
                        return desc
        except Exception:
            pass
    
    # Default descriptions based on directory name patterns
    if dir_name.lower() == 'src' or dir_name.lower() == 'source':
        return "Contains source code files for the project"
    elif dir_name.lower() == 'tests' or dir_name.lower() == 'test':
        return "Contains test files and test utilities"
    elif dir_name.lower() == 'docs' or dir_name.lower() == 'documentation':
        return "Contains documentation files"
    elif dir_name.lower() == 'examples' or dir_name.lower() == 'samples':
        return "Contains example code and usage demonstrations"
    elif dir_name.lower() == 'scripts':
        return "Contains utility scripts"
    elif dir_name.lower() == 'tools':
        return "Contains tools and utilities"
    elif dir_name.lower() == 'data' or dir_name.lower() == 'datas':
        return "Contains data files used by the project"
    elif dir_name.lower() == 'config' or dir_name.lower() == 'configuration':
        return "Contains configuration files"
    elif dir_name.lower() == 'lib' or dir_name.lower() == 'libs':
        return "Contains library files"
    elif dir_name.lower() == 'bin':
        return "Contains binary files and executables"
    elif dir_name.lower() == 'assets':
        return "Contains asset files like images, fonts, etc."
    elif dir_name.lower() == 'resources':
        return "Contains resource files used by the project"
    elif dir_name.lower() == 'templates':
        return "Contains template files"
    elif dir_name.lower() == 'static':
        return "Contains static files like CSS, JavaScript, images, etc."
    elif dir_name.lower() == 'public':
        return "Contains publicly accessible files"
    elif dir_name.lower() == 'private':
        return "Contains private files not meant for public access"
    elif dir_name.lower() == 'logs':
        return "Contains log files"
    elif dir_name.lower() == 'backups':
        return "Contains backup files"
    elif dir_name.lower() == 'temp' or dir_name.lower() == 'tmp':
        return "Contains temporary files"
    elif dir_name.lower() == 'build':
        return "Contains build artifacts"
    elif dir_name.lower() == 'dist':
        return "Contains distribution files"
    elif dir_name.lower() == 'node_modules':
        return "Contains Node.js dependencies"
    elif dir_name.lower() == 'venv' or dir_name.lower() == 'env':
        return "Contains Python virtual environment"
    elif dir_name.lower() == 'migrations':
        return "Contains database migration files"
    elif dir_name.lower() == 'fixtures':
        return "Contains test fixtures"
    elif dir_name.lower() == 'backtrader':
        return "Contains the core backtrader framework files"
    elif dir_name.lower() == 'strategies':
        return "Contains trading strategy implementations"
    elif dir_name.lower() == 'indicators':
        return "Contains technical indicator implementations"
    elif dir_name.lower() == 'analyzers':
        return "Contains performance analyzer implementations"
    elif dir_name.lower() == 'feeds':
        return "Contains data feed implementations"
    elif dir_name.lower() == 'brokers':
        return "Contains broker implementations"
    elif dir_name.lower() == 'observers':
        return "Contains observer implementations"
    elif dir_name.lower() == 'sizers':
        return "Contains position sizer implementations"
    elif dir_name.lower() == 'commissions':
        return "Contains commission scheme implementations"
    elif dir_name.lower() == 'filters':
        return "Contains data filter implementations"
    elif dir_name.lower() == 'signals':
        return "Contains signal implementations"
    elif dir_name.lower() == 'stores':
        return "Contains store implementations for data and broker connections"
    elif dir_name.lower() == 'utils':
        return "Contains utility functions and classes"
    elif dir_name.lower() == 'plot':
        return "Contains plotting functionality"
    elif dir_name.lower() == 'studies':
        return "Contains study implementations"
    elif dir_name.lower() == 'contrib':
        return "Contains contributed code from the community"
    elif dir_name.lower() == 'arbitrage':
        return "Contains arbitrage strategy implementations"
    elif dir_name.lower() == 'backtest':
        return "Contains backtesting functionality"
    elif dir_name.lower() == 'tutorials':
        return "Contains tutorial code and examples"
    elif dir_name.lower() == 'sandbox':
        return "Contains experimental or sandbox code"
    elif dir_name.lower() == 'reference':
        return "Contains reference materials and documentation"
    elif dir_name.lower() == 'outcome':
        return "Contains output and result files"
    elif dir_name.lower() == 'prompts':
        return "Contains prompt templates and configurations"
    elif dir_name.lower() == 'qmtbt':
        return "Contains QMT (Quantitative Model Toolkit) integration"
    elif dir_name.lower() == 'xtquant':
        return "Contains XTQuant integration"
    elif dir_name.lower() == 'turtle':
        return "Contains Turtle Trading strategy implementations"
    
    # If no specific description is found, create a generic one
    return f"Directory containing {dir_name.lower()} related files"

def format_docstring(docstring: str) -> str:
"""Format a docstring to follow Google style guide.
    
Args::
        docstring: The original docstring
        
Returns::
        str: The formatted docstring"""
    """
    if not docstring:
        return ""
    
    # Remove leading/trailing whitespace
    docstring = docstring.strip()
    
    # Check if it's already in Google style
    has_args_section = bool(re.search(r'Args:', docstring))
    has_returns_section = bool(re.search(r'Returns:', docstring))
    has_raises_section = bool(re.search(r'Raises:', docstring))
    
    # If it's already in Google style, just ensure proper indentation
    if has_args_section or has_returns_section or has_raises_section:
        lines = docstring.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Ensure sections are properly formatted
            if re.match(r'^\s*(Args|Returns|Raises|Note|Example|Examples|Attributes|Parameters):', line):
                # Ensure section headers have a blank line before them (unless it's the first line)
                if formatted_lines and formatted_lines[-1].strip():
                    formatted_lines.append('')
                formatted_lines.append(line.strip() + ':')
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    # Otherwise, try to convert to Google style
    # Extract parameter descriptions from the docstring
    param_matches = re.findall(r'@param\s+(\w+):\s*(.*?)(?=@|\Z)', docstring + '@', re.DOTALL)
    return_match = re.search(r'@return:\s*(.*?)(?=@|\Z)', docstring + '@', re.DOTALL)
    
    # If we found parameters or return values, convert to Google style
    if param_matches or return_match:
        # Start with the main description
        main_desc = re.sub(r'@param\s+\w+:.*', '', docstring)
        main_desc = re.sub(r'@return:.*', '', main_desc)
        main_desc = main_desc.strip()
        
        result = main_desc + '\n\n' if main_desc else ''
        
        # Add Args section if we have parameters
        if param_matches:
            result += 'Args:\n'
            for param, desc in param_matches:
                result += f'    {param}: {desc.strip()}\n'
            result += '\n'
        
        # Add Returns section if we have a return value
        if return_match:
            result += 'Returns:\n'
            result += f'    {return_match.group(1).strip()}\n'
        
        return result.strip()
    
    # If we couldn't identify a specific format, just return the cleaned docstring
    return docstring

def enhance_docstring(node: Union[ast.FunctionDef, ast.ClassDef, ast.Module], 
                     source_lines: List[str]) -> Optional[Tuple[int, int, str]]:
"""Enhance the docstring of a node (function, class, or module).
    
Args::
        node: The AST node
        source_lines: The source code lines
        
Returns::
        Optional[Tuple[int, int, str]]: Start line, end line, and enhanced docstring if changes needed"""
    """
    # Check if the node has a docstring
    if not (node.body and isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Str)):
        # No docstring, create a basic one
        if isinstance(node, ast.FunctionDef):
            # For functions/methods
            args = [arg.arg for arg in node.args.args if arg.arg != 'self']
            returns_value = not (isinstance(node.returns, ast.NameConstant) and node.returns.value is None)
            
            docstring = f"{node.name} function.\n\n"
            
            if args:
                docstring += "Args:\n"
                for arg in args:
                    docstring += f"    {arg}: Description of {arg}\n"
                docstring += "\n"
            
            if returns_value:
                docstring += "Returns:\n    Description of return value\n"
            
            # Insert at the beginning of the function body
            start_line = node.lineno
            end_line = node.lineno
            return start_line, end_line, f'"""{docstring}"""'
        
        elif isinstance(node, ast.ClassDef):
            # For classes
            docstring = f"{node.name} class.\n\nDescription of the class functionality."
            
            # Insert at the beginning of the class body
            start_line = node.lineno
            end_line = node.lineno
            return start_line, end_line, f'"""{docstring}"""'
        
        elif isinstance(node, ast.Module):
            # For modules
            filename = getattr(node, 'filename', 'module')
            docstring = f"{os.path.basename(filename)} module.\n\nDescription of the module functionality."
            
            # Insert at the beginning of the file
            return 1, 1, f'"""{docstring}"""\n'
        
        return None
    
    # Get the existing docstring
    docstring_node = node.body[0].value
    docstring = docstring_node.s
    
    # Format the docstring
    enhanced_docstring = format_docstring(docstring)
    
    # If the docstring hasn't changed, return None
    if enhanced_docstring == docstring:
        return None
    
    # Get the start and end lines of the docstring
    start_line = docstring_node.lineno
    end_line = start_line
    for i, line in enumerate(source_lines[start_line:], start=start_line):
        if '"""' in line and i > start_line:
            end_line = i
            break
    
    # Return the enhanced docstring with proper triple quotes
    return start_line, end_line, f'"""{enhanced_docstring}"""'

def process_python_file(file_path: str) -> None:
"""Process a Python file to enhance its documentation.
    
Args::
        file_path: Path to the Python file"""
    """
    print(f"Processing {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
            source_lines = source.split('\n')
        
        # Parse the source code
        tree = ast.parse(source)
        tree.filename = file_path  # Add filename attribute for reference
        
        # Collect all nodes that might have docstrings
        nodes_to_process = []
        
        # Add the module itself
        nodes_to_process.append(tree)
        
        # Add all classes and functions
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                nodes_to_process.append(node)
        
        # Process each node
        changes = []
        for node in nodes_to_process:
            result = enhance_docstring(node, source_lines)
            if result:
                changes.append(result)
        
        # Apply changes in reverse order (bottom to top) to avoid line number issues
        if changes:
            changes.sort(reverse=True)
            
            # Create a new version of the source code with enhanced docstrings
            new_source_lines = source_lines.copy()
            for start_line, end_line, new_docstring in changes:
                # Replace the old docstring with the new one
                new_source_lines[start_line-1:end_line] = [new_docstring]
            
            # Write the changes back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_source_lines))
            
            print(f"Enhanced documentation in {file_path}")
        else:
            print(f"No changes needed for {file_path}")
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def create_readme(dir_path: str, root_path: str) -> None:
"""Create or update a README.md file for the given directory.
    
Args::
        dir_path: Path to the directory
        root_path: Path to the repository root"""
    """
    # Skip excluded directories
    dir_name = os.path.basename(dir_path)
    if dir_name in EXCLUDE_DIRS:
        return
    
    # Get relative path from root
    rel_path = os.path.relpath(dir_path, root_path)
    if rel_path == '.':
        rel_path = ''
    
    # Get parent directory path
    parent_dir = os.path.dirname(dir_path)
    parent_rel_path = os.path.relpath(parent_dir, root_path)
    if parent_rel_path == '.':
        parent_rel_path = ''
    
    # Get directory description
    dir_description = get_directory_description(dir_path)
    
    # Get subdirectories
    subdirs = []
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if os.path.isdir(item_path) and item not in EXCLUDE_DIRS and not item.startswith('.'):
            subdirs.append(item)
    subdirs.sort()
    
    # Get files
    files = []
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if os.path.isfile(item_path) and item != 'README.md' and not item.startswith('.'):
            files.append(item)
    files.sort()
    
    # Count file types
    file_types = {}
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext:
            file_types[ext] = file_types.get(ext, 0) + 1
    
    # Create README content
    content = f"# {dir_name}\n\n"
    content += f"{dir_description}\n\n"
    
    # Add navigation section
    content += "## Navigation\n\n"
    content += f"* [🏠 Root Directory]({os.path.join('/', rel_path, '..') * (rel_path.count('/') + 1) if rel_path else './'}README.md)\n"
    
    if parent_rel_path:
        parent_name = os.path.basename(parent_dir)
        content += f"* [⬆️ Parent Directory ({parent_name})]({os.path.join('..', 'README.md')})\n"
    
    # Add subdirectories section if there are any
    if subdirs:
        content += "\n### Subdirectories\n\n"
        for subdir in subdirs:
            subdir_path = os.path.join(dir_path, subdir)
            subdir_desc = get_directory_description(subdir_path)
            # Take first sentence or up to 100 characters
            short_desc = re.split(r'\.(?:\s|$)', subdir_desc)[0].strip()
            if len(short_desc) > 100:
                short_desc = short_desc[:97] + "..."
            content += f"* [{subdir}]({os.path.join(subdir, 'README.md')}) - {short_desc}\n"
    
    # Add files section if there are any
    if files:
        content += "\n## Files\n\n"
        for file in files:
            file_path = os.path.join(dir_path, file)
            file_desc = get_file_description(file_path)
            content += f"### {file}\n\n"
            content += f"{file_desc}\n\n"
    
    # Add directory summary
    content += "## Directory Summary\n\n"
    content += f"This directory contains {len(files)} files and {len(subdirs)} subdirectories.\n\n"
    
    # Add file types summary if there are any
    if file_types:
        content += "### File Types\n\n"
        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            content += f"* {ext}: {count} files\n"
    
    # Write README.md file
    readme_path = os.path.join(dir_path, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Created/Updated README.md in {rel_path or '.'}")

def enhance_python_docstrings(file_path: str) -> None:
"""Enhance docstrings in a Python file to follow Google style guide.
    
Args::
        file_path: Path to the Python file"""
    """
    # Use the more robust process_python_file function
    process_python_file(file_path)

def process_directory(dir_path: str, root_path: str) -> None:
"""Process a directory and its subdirectories recursively.
    
Args::
        dir_path: Path to the directory
        root_path: Path to the repository root"""
    """
    # Create README.md for current directory
    create_readme(dir_path, root_path)
    
    # Process Python files in the directory
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if os.path.isfile(item_path) and item.endswith('.py'):
            enhance_python_docstrings(item_path)
    
    # Process subdirectories
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if os.path.isdir(item_path) and item not in EXCLUDE_DIRS and not item.startswith('.'):
            process_directory(item_path, root_path)

def main() -> None:
    """Main function to process the repository."""
    # Get repository root path
    root_path = os.getcwd()
    
    print(f"Starting to process repository at {root_path}")
    
    # Process the repository
    process_directory(root_path, root_path)
    
    print("Finished processing repository")

if __name__ == "__main__":
    main()