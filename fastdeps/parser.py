"""AST-based import extraction - NEVER executes code"""

import ast
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set


@dataclass
class Import:
    """Represents a Python import statement"""
    module: Optional[str]  # Module name (e.g., "os.path")
    names: List[str]       # Imported names (e.g., ["join", "exists"])
    level: int             # Relative import level (0 = absolute)
    line: int              # Line number in source file
    is_from: bool          # True for "from X import Y"


class ImportExtractor:
    """Extract imports using AST parsing - safe and fast"""

    def __init__(self, max_initial_bytes: int = 10240):
        """
        Args:
            max_initial_bytes: Read this many bytes first (most imports at top)
        """
        self.max_initial_bytes = max_initial_bytes

    def extract_imports(self, file_path: Path) -> List[Import]:
        """
        Extract all imports from a Python file using AST.

        Never executes code - only parses.
        """
        if not file_path.exists():
            return []

        try:
            # Try reading just the beginning first (fast path)
            source = self._read_source(file_path, truncate=True)
            tree = ast.parse(source)
        except SyntaxError:
            # If truncated incorrectly, read full file
            try:
                source = self._read_source(file_path, truncate=False)
                tree = ast.parse(source)
            except SyntaxError:
                # File has syntax errors - return empty
                return []

        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # import os, sys
                for alias in node.names:
                    imports.append(Import(
                        module=alias.name,
                        names=[],
                        level=0,
                        line=node.lineno,
                        is_from=False
                    ))

            elif isinstance(node, ast.ImportFrom):
                # from os.path import join, exists
                # from . import utils
                # from ..package import module
                module = node.module or ""
                level = node.level or 0

                if node.names[0].name == "*":
                    # from module import *
                    names = ["*"]
                else:
                    names = [alias.name for alias in node.names]

                imports.append(Import(
                    module=module,
                    names=names,
                    level=level,
                    line=node.lineno,
                    is_from=True
                ))

        return imports

    def _read_source(self, file_path: Path, truncate: bool) -> str:
        """Read Python source file"""
        try:
            with open(file_path, 'rb') as f:
                if truncate:
                    source_bytes = f.read(self.max_initial_bytes)
                else:
                    source_bytes = f.read()

            # Try UTF-8 first, fallback to latin-1
            try:
                return source_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return source_bytes.decode('latin-1', errors='replace')
        except Exception:
            return ""


def find_python_files(root_path: Path, exclude_dirs: Set[str] = None, ignore_patterns: List[str] = None) -> List[Path]:
    """
    Fast discovery of Python files using os.scandir (faster than Path.rglob)

    Args:
        root_path: Root directory to search
        exclude_dirs: Directory names to exclude
        ignore_patterns: Glob patterns to ignore (e.g., "test_*.py", "**/tests/**", "*.pyc")
    """
    import fnmatch

    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', '.venv', 'venv', 'env',
                        'node_modules', '.tox', '.mypy_cache', '.pytest_cache'}

    if ignore_patterns is None:
        ignore_patterns = []

    python_files = []
    dirs_to_process = [root_path]

    def should_ignore(path: Path) -> bool:
        """Check if path matches any ignore pattern"""
        # Convert to relative path from root
        try:
            rel_path = path.relative_to(root_path)
        except ValueError:
            rel_path = path

        str_path = str(rel_path)

        for pattern in ignore_patterns:
            # Handle ** patterns for recursive matching
            if '**' in pattern:
                # Convert ** to match any path depth
                pattern_regex = pattern.replace('**/', '*/').replace('**', '*')
                if fnmatch.fnmatch(str_path, pattern_regex):
                    return True
                # Also check each path component
                for part in rel_path.parts:
                    if fnmatch.fnmatch(part, pattern.replace('**/', '').replace('**', '*')):
                        return True
            else:
                # Simple pattern matching
                if fnmatch.fnmatch(str_path, pattern):
                    return True
                # Also check just the filename
                if fnmatch.fnmatch(path.name, pattern):
                    return True

        return False

    while dirs_to_process:
        current_dir = dirs_to_process.pop()

        # Check if entire directory should be ignored
        if should_ignore(current_dir):
            continue

        try:
            with os.scandir(current_dir) as entries:
                for entry in entries:
                    entry_path = Path(entry.path)

                    # Skip hidden and excluded directories
                    if entry.name.startswith('.') and entry.is_dir():
                        continue
                    if entry.name in exclude_dirs:
                        continue

                    # Check ignore patterns
                    if should_ignore(entry_path):
                        continue

                    if entry.is_file() and entry.name.endswith('.py'):
                        python_files.append(entry_path)
                    elif entry.is_dir() and not entry.is_symlink():
                        dirs_to_process.append(entry_path)
        except (PermissionError, OSError):
            # Skip directories we can't read
            continue

    return python_files