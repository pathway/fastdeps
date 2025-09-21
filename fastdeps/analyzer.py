"""Main dependency analyzer - orchestrates the analysis pipeline"""

import time
from pathlib import Path
from typing import Optional, List, Set

from .parser import ImportExtractor, find_python_files
from .parallel import ParallelProcessor
from .resolver import ModuleResolver
from .graph import DependencyGraph


class DependencyAnalyzer:
    """Main analyzer that coordinates all components"""

    def __init__(self, num_workers: int = None, exclude_dirs: Set[str] = None, ignore_patterns: List[str] = None):
        """
        Args:
            num_workers: Number of parallel workers
            exclude_dirs: Directories to exclude from analysis
            ignore_patterns: Glob patterns to ignore files/folders
        """
        self.num_workers = num_workers
        self.exclude_dirs = exclude_dirs
        self.ignore_patterns = ignore_patterns or []

    def analyze(self, target: str, internal_only: bool = False) -> DependencyGraph:
        """
        Analyze dependencies for a target.

        Args:
            target: Path to file, directory, or module name
            internal_only: If True, ignore external dependencies

        Returns:
            DependencyGraph with all dependencies
        """
        start_time = time.time()

        # Resolve target to path
        target_path = Path(target).resolve()

        if not target_path.exists():
            raise FileNotFoundError(f"Target not found: {target}")

        # Determine what to analyze
        if target_path.is_file():
            # Single file
            files_to_analyze = [target_path]
            root_path = target_path.parent
        else:
            # Directory/package
            files_to_analyze = find_python_files(target_path, self.exclude_dirs, self.ignore_patterns)
            root_path = target_path

        print(f"Found {len(files_to_analyze)} Python files to analyze")

        # Extract imports from all files (parallel)
        processor = ParallelProcessor(self.num_workers)
        file_imports = processor.process_files(files_to_analyze)

        print(f"Extracted imports from {len(file_imports)} files")

        # Build module resolver
        resolver = ModuleResolver(root_path)

        # Build dependency graph
        graph = DependencyGraph()
        graph.root_path = root_path

        for file_path, imports in file_imports.items():
            # Add file to graph
            graph.add_file(file_path)

            # Resolve each import
            for imp in imports:
                if imp.level == 0:
                    # Absolute import
                    resolved = resolver.resolve_import(imp.module, file_path)
                else:
                    # Relative import
                    # For "from . import X", use X as module name
                    module_name = imp.names[0] if not imp.module and imp.names else imp.module
                    resolved = resolver.resolve_import(module_name, file_path, imp.level)

                if resolved:
                    # Internal dependency
                    graph.add_dependency(file_path, resolved)
                elif not internal_only and imp.module:
                    # External dependency
                    if resolver.is_external(imp.module):
                        graph.add_external(file_path, imp.module)

        elapsed = time.time() - start_time
        print(f"Analysis complete in {elapsed:.2f} seconds")

        # Print stats
        stats = graph.get_stats()
        print(f"  Files: {stats['total_files']}")
        print(f"  Dependencies: {stats['total_dependencies']}")
        print(f"  External: {stats['total_external']}")
        print(f"  Cycles: {stats['cycles']}")

        return graph