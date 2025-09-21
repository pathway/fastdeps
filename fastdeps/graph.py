"""Dependency graph structure and algorithms"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


@dataclass
class Node:
    """A node in the dependency graph"""
    path: Path
    imports: Set[Path] = field(default_factory=set)
    imported_by: Set[Path] = field(default_factory=set)
    external_imports: Set[str] = field(default_factory=set)


class DependencyGraph:
    """Graph structure for dependencies"""

    def __init__(self):
        self.nodes: Dict[Path, Node] = {}
        self.root_path: Optional[Path] = None

    def add_file(self, file_path: Path):
        """Add a file to the graph"""
        if file_path not in self.nodes:
            self.nodes[file_path] = Node(path=file_path)

    def add_dependency(self, from_file: Path, to_file: Path):
        """Add a dependency edge"""
        # Ensure both nodes exist
        self.add_file(from_file)
        self.add_file(to_file)

        # Add edge
        self.nodes[from_file].imports.add(to_file)
        self.nodes[to_file].imported_by.add(from_file)

    def add_external(self, from_file: Path, module_name: str):
        """Add an external dependency"""
        self.add_file(from_file)
        self.nodes[from_file].external_imports.add(module_name)

    def find_cycles(self) -> List[List[Path]]:
        """
        Find all circular dependencies using Tarjan's algorithm.

        Returns list of cycles (each cycle is a list of paths).
        """
        index = 0
        stack = []
        indices = {}
        lowlinks = {}
        on_stack = set()
        cycles = []

        def strongconnect(node_path: Path):
            nonlocal index

            indices[node_path] = index
            lowlinks[node_path] = index
            index += 1
            stack.append(node_path)
            on_stack.add(node_path)

            # Check successors
            if node_path in self.nodes:
                for neighbor in self.nodes[node_path].imports:
                    if neighbor not in indices:
                        strongconnect(neighbor)
                        lowlinks[node_path] = min(lowlinks[node_path],
                                                 lowlinks[neighbor])
                    elif neighbor in on_stack:
                        lowlinks[node_path] = min(lowlinks[node_path],
                                                 indices[neighbor])

            # If node is a root, pop the stack and create SCC
            if lowlinks[node_path] == indices[node_path]:
                component = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    component.append(w)
                    if w == node_path:
                        break

                # Only report actual cycles (more than 1 node)
                if len(component) > 1:
                    # Check if it's a real cycle (not just mutual imports)
                    if self._is_real_cycle(component):
                        cycles.append(component)

        # Run algorithm on all nodes
        for node_path in self.nodes:
            if node_path not in indices:
                strongconnect(node_path)

        return cycles

    def _is_real_cycle(self, component: List[Path]) -> bool:
        """Check if component forms a real cycle"""
        # For each node in component, check if it can reach itself
        for start in component:
            visited = set()
            queue = deque([start])

            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)

                if current in self.nodes:
                    for neighbor in self.nodes[current].imports:
                        if neighbor == start and current != start:
                            return True  # Found cycle back to start
                        if neighbor in component and neighbor not in visited:
                            queue.append(neighbor)

        return False

    def get_stats(self) -> Dict:
        """Get graph statistics"""
        total_files = len(self.nodes)
        total_deps = sum(len(node.imports) for node in self.nodes.values())
        total_external = sum(len(node.external_imports)
                           for node in self.nodes.values())

        # Find most imported files
        import_counts = defaultdict(int)
        for node in self.nodes.values():
            for imp in node.imports:
                import_counts[imp] += 1

        most_imported = sorted(import_counts.items(),
                              key=lambda x: x[1], reverse=True)[:5]

        # Find files with most imports
        most_imports = sorted([(path, len(node.imports))
                              for path, node in self.nodes.items()],
                             key=lambda x: x[1], reverse=True)[:5]

        return {
            'total_files': total_files,
            'total_dependencies': total_deps,
            'total_external': total_external,
            'cycles': len(self.find_cycles()),
            'most_imported': most_imported,
            'most_imports': most_imports,
        }

    def to_dict(self) -> Dict:
        """Convert graph to dictionary for JSON serialization"""
        result = {
            'nodes': {},
            'edges': [],
            'external': {},
        }

        for file_path, node in self.nodes.items():
            # Make paths relative for cleaner output
            rel_path = file_path.relative_to(self.root_path) if self.root_path else file_path

            result['nodes'][str(rel_path)] = {
                'imports_count': len(node.imports),
                'imported_by_count': len(node.imported_by),
                'external_count': len(node.external_imports),
            }

            # Add edges
            for imported in node.imports:
                rel_imported = imported.relative_to(self.root_path) if self.root_path else imported
                result['edges'].append({
                    'from': str(rel_path),
                    'to': str(rel_imported),
                })

            # Add external deps
            if node.external_imports:
                result['external'][str(rel_path)] = sorted(node.external_imports)

        return result