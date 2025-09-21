"""Parallel processing for maximum speed"""

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List
import os

from .parser import ImportExtractor, Import


def process_chunk(file_paths: List[Path]) -> Dict[Path, List[Import]]:
    """
    Worker function to process a chunk of files.
    Runs in separate process for true parallelism.
    """
    extractor = ImportExtractor()
    results = {}

    for file_path in file_paths:
        try:
            imports = extractor.extract_imports(file_path)
            results[file_path] = imports
        except Exception:
            # Don't let one bad file break everything
            results[file_path] = []

    return results


class ParallelProcessor:
    """Process files in parallel for maximum speed"""

    def __init__(self, num_workers: int = None):
        """
        Args:
            num_workers: Number of parallel workers (default: CPU count)
        """
        self.num_workers = num_workers or mp.cpu_count()

    def process_files(self, file_paths: List[Path]) -> Dict[Path, List[Import]]:
        """
        Process multiple files in parallel.

        Returns dict mapping file paths to their imports.
        """
        if not file_paths:
            return {}

        # For small numbers of files, parallel overhead isn't worth it
        if len(file_paths) <= 3:
            return process_chunk(file_paths)

        # Split into chunks for better load balancing
        chunk_size = max(1, len(file_paths) // (self.num_workers * 4))
        chunks = []
        for i in range(0, len(file_paths), chunk_size):
            chunks.append(file_paths[i:i + chunk_size])

        # Process chunks in parallel
        all_results = {}

        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit all chunks
            futures = {executor.submit(process_chunk, chunk): chunk
                      for chunk in chunks}

            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    chunk_results = future.result(timeout=30)
                    all_results.update(chunk_results)
                except Exception:
                    # If a chunk fails, mark files as failed
                    chunk = futures[future]
                    for file_path in chunk:
                        all_results[file_path] = []

        return all_results