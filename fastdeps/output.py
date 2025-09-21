"""Output formatters for dependency graphs"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .graph import DependencyGraph


class GraphRenderer:
    """Render dependency graphs in various formats"""

    def __init__(self, graph: DependencyGraph):
        self.graph = graph

    def to_dot(self, show_external: bool = False) -> str:
        """
        Generate Graphviz DOT format.

        Args:
            show_external: If True, include external dependencies

        Returns:
            DOT format string
        """
        lines = ["digraph dependencies {"]
        lines.append('    rankdir="LR";')
        lines.append('    node [shape=box];')
        lines.append("")

        # Add nodes
        for file_path, node in self.graph.nodes.items():
            rel_path = file_path.relative_to(self.graph.root_path) if self.graph.root_path else file_path
            label = str(rel_path).replace('/', '\\n')

            # Color based on characteristics
            if node.imported_by and not node.imports:
                # Leaf node (imported but doesn't import)
                color = "lightgreen"
            elif node.imports and not node.imported_by:
                # Root node (imports but not imported)
                color = "lightblue"
            elif len(node.imported_by) > 3:
                # Heavily used module
                color = "yellow"
            else:
                color = "white"

            lines.append(f'    "{rel_path}" [label="{label}", fillcolor="{color}", style=filled];')

        lines.append("")

        # Add edges for internal dependencies
        for file_path, node in self.graph.nodes.items():
            from_path = file_path.relative_to(self.graph.root_path) if self.graph.root_path else file_path

            for imported_path in node.imports:
                to_path = imported_path.relative_to(self.graph.root_path) if self.graph.root_path else imported_path
                lines.append(f'    "{from_path}" -> "{to_path}";')

        # Add external dependencies if requested
        if show_external:
            lines.append("")
            lines.append("    // External dependencies")

            for file_path, node in self.graph.nodes.items():
                if node.external_imports:
                    from_path = file_path.relative_to(self.graph.root_path) if self.graph.root_path else file_path

                    for ext_module in node.external_imports:
                        ext_node = f"ext_{ext_module.replace('.', '_')}"
                        lines.append(f'    {ext_node} [label="{ext_module}", shape=ellipse, style=dashed];')
                        lines.append(f'    "{from_path}" -> {ext_node} [style=dashed];')

        lines.append("}")
        return "\n".join(lines)

    def to_json(self) -> str:
        """Generate JSON representation"""
        return json.dumps(self.graph.to_dict(), indent=2)

    def to_text(self) -> str:
        """Generate human-readable text tree"""
        lines = ["Dependency Analysis Report", "=" * 50, ""]

        stats = self.graph.get_stats()

        # Summary stats
        lines.append(f"Files analyzed: {stats['total_files']}")
        lines.append(f"Internal dependencies: {stats['total_dependencies']}")
        lines.append(f"External dependencies: {stats['total_external']}")
        lines.append(f"Circular dependencies: {stats['cycles']}")
        lines.append("")

        # Most imported files
        if stats['most_imported']:
            lines.append("Most imported files:")
            for path, count in stats['most_imported']:
                rel_path = path.relative_to(self.graph.root_path) if self.graph.root_path else path
                lines.append(f"  {rel_path}: {count} imports")
            lines.append("")

        # Files with most imports
        if stats['most_imports']:
            lines.append("Files with most imports:")
            for path, count in stats['most_imports']:
                rel_path = path.relative_to(self.graph.root_path) if self.graph.root_path else path
                lines.append(f"  {rel_path}: {count} imports")
            lines.append("")

        # Circular dependencies
        cycles = self.graph.find_cycles()
        if cycles:
            lines.append("⚠️  Circular dependencies detected:")
            for i, cycle in enumerate(cycles, 1):
                lines.append(f"  Cycle {i}:")
                for file_path in cycle:
                    rel_path = file_path.relative_to(self.graph.root_path) if self.graph.root_path else file_path
                    lines.append(f"    → {rel_path}")
            lines.append("")

        return "\n".join(lines)

    def save_dot(self, output_path: Path, show_external: bool = False):
        """Save graph as DOT file"""
        dot_content = self.to_dot(show_external)
        output_path.write_text(dot_content)

    def save_png(self, output_path: Path, show_external: bool = False,
                 show: bool = False):
        """
        Save graph as PNG using Graphviz.

        Args:
            output_path: Where to save the PNG
            show_external: Include external dependencies
            show: If True, open the PNG after generation
        """
        # Generate DOT content
        dot_content = self.to_dot(show_external)

        # Create temp DOT file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(dot_content)
            dot_file = f.name

        try:
            # Run Graphviz dot command
            cmd = ['dot', '-Tpng', dot_file, '-o', str(output_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"Error generating PNG: {result.stderr}")
                return False

            print(f"Generated PNG: {output_path}")

            # Open the image if requested
            if show:
                # Try different viewers
                for viewer in ['xdg-open', 'open', 'start']:
                    try:
                        subprocess.run([viewer, str(output_path)],
                                     capture_output=True, check=False)
                        break
                    except FileNotFoundError:
                        continue

            return True

        except FileNotFoundError:
            print("Error: Graphviz 'dot' command not found.")
            print("Install with: apt-get install graphviz (Linux) or brew install graphviz (Mac)")
            return False

        finally:
            # Clean up temp file
            Path(dot_file).unlink(missing_ok=True)

    def save_svg(self, output_path: Path, show_external: bool = False):
        """Save graph as SVG using Graphviz"""
        dot_content = self.to_dot(show_external)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(dot_content)
            dot_file = f.name

        try:
            cmd = ['dot', '-Tsvg', dot_file, '-o', str(output_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"Generated SVG: {output_path}")
                return True
            else:
                print(f"Error generating SVG: {result.stderr}")
                return False

        except FileNotFoundError:
            print("Error: Graphviz 'dot' command not found.")
            return False

        finally:
            Path(dot_file).unlink(missing_ok=True)