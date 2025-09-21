"""Module resolution - convert imports to actual file paths"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional, Set, List


class ModuleResolver:
    """Resolve import statements to actual files"""

    # Python stdlib modules (not exhaustive, but common ones)
    STDLIB_MODULES = {
        'abc', 'argparse', 'ast', 'asyncio', 'base64', 'bisect', 'builtins',
        'collections', 'contextlib', 'copy', 'csv', 'dataclasses', 'datetime',
        'decimal', 'dis', 'enum', 'functools', 'gc', 'glob', 'hashlib', 'heapq',
        'http', 'importlib', 'inspect', 'io', 'itertools', 'json', 'logging',
        'math', 'multiprocessing', 'os', 'pathlib', 'pickle', 'platform', 'queue',
        'random', 're', 'shutil', 'signal', 'socket', 'sqlite3', 'string',
        'struct', 'subprocess', 'sys', 'tempfile', 'textwrap', 'threading',
        'time', 'timeit', 'traceback', 'typing', 'unittest', 'urllib', 'uuid',
        'warnings', 'weakref', 'xml', 'zipfile',
    }

    def __init__(self, root_path: Path):
        """
        Args:
            root_path: Project root directory
        """
        self.root_path = root_path.resolve()
        self.file_index: Dict[str, Path] = {}
        self.package_dirs: Set[Path] = set()
        self._build_index()

    def _build_index(self):
        """Build an index of all Python modules in the project"""
        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)

            # Check if this is a package (has __init__.py)
            if '__init__.py' in files:
                self.package_dirs.add(root_path)

            # Index all Python files
            for file in files:
                if file.endswith('.py'):
                    file_path = root_path / file
                    # Convert file path to module path
                    try:
                        rel_path = file_path.relative_to(self.root_path)
                        module_path = self._path_to_module(rel_path)
                        self.file_index[module_path] = file_path
                    except ValueError:
                        # File outside root - skip
                        pass

    def _path_to_module(self, rel_path: Path) -> str:
        """Convert file path to module name"""
        # Remove .py extension
        if rel_path.suffix == '.py':
            if rel_path.stem == '__init__':
                # Package __init__.py - just use directory path
                parts = rel_path.parts[:-1]
            else:
                # Regular module
                parts = list(rel_path.parts[:-1]) + [rel_path.stem]
        else:
            parts = rel_path.parts

        return '.'.join(parts) if parts else ""

    def resolve_import(self, module_name: str, from_file: Path,
                      level: int = 0) -> Optional[Path]:
        """
        Resolve an import to a file path.

        Args:
            module_name: The module being imported
            from_file: The file doing the importing
            level: Relative import level (0 = absolute)

        Returns:
            Path to the resolved file, or None if external/stdlib
        """
        if level == 0:
            # Absolute import
            return self._resolve_absolute(module_name, from_file)
        else:
            # Relative import
            return self._resolve_relative(module_name, from_file, level)

    def _resolve_absolute(self, module_name: str, from_file: Path = None) -> Optional[Path]:
        """Resolve absolute import"""
        if not module_name:
            return None

        # Check if it's a known stdlib module
        top_level = module_name.split('.')[0]
        if top_level in self.STDLIB_MODULES:
            return None  # Stdlib - no file path

        # If module starts with the root package name, strip it
        # e.g., "gaia_elf_v3.agsearch_elf_v2" -> "agsearch_elf_v2"
        if self.root_path and self.root_path.name == top_level:
            stripped_module = '.'.join(module_name.split('.')[1:]) if '.' in module_name else ''
            if stripped_module:
                # Try with stripped version first
                if stripped_module in self.file_index:
                    return self.file_index[stripped_module]
                stripped_init = f"{stripped_module}.__init__"
                if stripped_init in self.file_index:
                    return self.file_index[stripped_init]

        # Try direct module lookup
        if module_name in self.file_index:
            return self.file_index[module_name]

        # Try as package __init__.py
        package_init = f"{module_name}.__init__"
        if package_init in self.file_index:
            return self.file_index[package_init]

        # If we have from_file, also try looking in the same package
        if from_file:
            try:
                from_rel = from_file.relative_to(self.root_path)
                from_parts = list(from_rel.parts[:-1])  # Get directory parts

                # Try module as sibling in same directory
                if from_parts:
                    sibling_module = '.'.join(from_parts + [module_name])
                    if sibling_module in self.file_index:
                        return self.file_index[sibling_module]

                    # Try as sibling package __init__.py
                    sibling_init = f"{sibling_module}.__init__"
                    if sibling_init in self.file_index:
                        return self.file_index[sibling_init]

                # Also try resolving within parent package
                # e.g., from gaia_airflow/dags/file.py, "utils.x" -> "gaia_airflow.utils.x"
                if len(from_parts) > 1:
                    # Try one level up
                    parent_parts = from_parts[:-1]
                    parent_module = '.'.join(parent_parts + module_name.split('.'))
                    if parent_module in self.file_index:
                        return self.file_index[parent_module]
                    parent_init = f"{parent_module}.__init__"
                    if parent_init in self.file_index:
                        return self.file_index[parent_init]
            except ValueError:
                pass

        # Try parent packages
        parts = module_name.split('.')
        for i in range(len(parts) - 1, 0, -1):
            parent = '.'.join(parts[:i])
            if parent in self.file_index:
                # Found parent module
                return self.file_index[parent]
            parent_init = f"{parent}.__init__"
            if parent_init in self.file_index:
                return self.file_index[parent_init]

        return None  # External dependency

    def _resolve_relative(self, module_name: str, from_file: Path,
                          level: int) -> Optional[Path]:
        """Resolve relative import"""
        try:
            # Get the package containing from_file
            from_rel = from_file.relative_to(self.root_path)
            from_parts = list(from_rel.parts)

            # If from __init__.py, package is the directory
            if from_rel.stem == '__init__':
                from_parts = from_parts[:-1]
            else:
                # Regular module - package is parent directory
                from_parts = from_parts[:-1]

            # Go up 'level-1' directories (level=1 means current package)
            if level > len(from_parts) + 1:
                # Too many levels - invalid import
                return None

            if level > 1:
                # Go up level-1 directories
                from_parts = from_parts[:-(level - 1)] if len(from_parts) >= level - 1 else []

            # Append the module name
            if module_name:
                target_parts = from_parts + module_name.split('.')
            else:
                target_parts = from_parts

            # Try to resolve
            target_module = '.'.join(target_parts) if target_parts else ""
            if target_module in self.file_index:
                return self.file_index[target_module]

            # Try as package
            if target_module:
                target_init = f"{target_module}"
                if target_init in self.file_index:
                    return self.file_index[target_init]

        except (ValueError, IndexError):
            pass

        return None

    def is_external(self, module_name: str) -> bool:
        """Check if module is external (not in project or stdlib)"""
        if not module_name:
            return False

        top_level = module_name.split('.')[0]

        # Check stdlib
        if top_level in self.STDLIB_MODULES:
            return False

        # Check if in our project
        if module_name in self.file_index:
            return False

        # Check package
        if f"{module_name}.__init__" in self.file_index:
            return False

        return True