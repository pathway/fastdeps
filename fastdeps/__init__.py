"""FastDeps - Lightning-fast Python dependency analyzer"""

__version__ = "1.0.0"

from .analyzer import DependencyAnalyzer
from .graph import DependencyGraph

__all__ = ["DependencyAnalyzer", "DependencyGraph"]