"""Tests for dependency graph"""

import unittest
from pathlib import Path

from fastdeps.graph import DependencyGraph, Node


class TestDependencyGraph(unittest.TestCase):
    """Test dependency graph operations"""

    def setUp(self):
        self.graph = DependencyGraph()

    def test_add_file(self):
        """Test adding files to graph"""
        file1 = Path("/project/main.py")
        self.graph.add_file(file1)

        self.assertIn(file1, self.graph.nodes)
        self.assertIsInstance(self.graph.nodes[file1], Node)

    def test_add_dependency(self):
        """Test adding dependency edge"""
        file1 = Path("/project/main.py")
        file2 = Path("/project/utils.py")

        self.graph.add_dependency(file1, file2)

        # Both files should be in graph
        self.assertIn(file1, self.graph.nodes)
        self.assertIn(file2, self.graph.nodes)

        # Check edge exists
        self.assertIn(file2, self.graph.nodes[file1].imports)
        self.assertIn(file1, self.graph.nodes[file2].imported_by)

    def test_add_external(self):
        """Test adding external dependency"""
        file1 = Path("/project/main.py")
        self.graph.add_external(file1, "requests")

        self.assertIn(file1, self.graph.nodes)
        self.assertIn("requests", self.graph.nodes[file1].external_imports)

    def test_simple_cycle_detection(self):
        """Test detecting simple A -> B -> A cycle"""
        a = Path("/project/a.py")
        b = Path("/project/b.py")

        self.graph.add_dependency(a, b)
        self.graph.add_dependency(b, a)

        cycles = self.graph.find_cycles()

        self.assertEqual(len(cycles), 1)
        cycle_files = set(cycles[0])
        self.assertEqual(cycle_files, {a, b})

    def test_three_node_cycle(self):
        """Test detecting A -> B -> C -> A cycle"""
        a = Path("/project/a.py")
        b = Path("/project/b.py")
        c = Path("/project/c.py")

        self.graph.add_dependency(a, b)
        self.graph.add_dependency(b, c)
        self.graph.add_dependency(c, a)

        cycles = self.graph.find_cycles()

        self.assertEqual(len(cycles), 1)
        cycle_files = set(cycles[0])
        self.assertEqual(cycle_files, {a, b, c})

    def test_no_cycle(self):
        """Test no false positives for cycle detection"""
        a = Path("/project/a.py")
        b = Path("/project/b.py")
        c = Path("/project/c.py")

        # Linear dependencies: A -> B -> C
        self.graph.add_dependency(a, b)
        self.graph.add_dependency(b, c)

        cycles = self.graph.find_cycles()

        self.assertEqual(len(cycles), 0)

    def test_multiple_cycles(self):
        """Test detecting multiple independent cycles"""
        # Cycle 1: a -> b -> a
        a = Path("/project/a.py")
        b = Path("/project/b.py")
        self.graph.add_dependency(a, b)
        self.graph.add_dependency(b, a)

        # Cycle 2: c -> d -> c
        c = Path("/project/c.py")
        d = Path("/project/d.py")
        self.graph.add_dependency(c, d)
        self.graph.add_dependency(d, c)

        cycles = self.graph.find_cycles()

        self.assertEqual(len(cycles), 2)

    def test_self_import(self):
        """Test self-import is not reported as cycle"""
        a = Path("/project/a.py")
        self.graph.add_dependency(a, a)

        cycles = self.graph.find_cycles()

        # Self-import is weird but not a multi-file cycle
        self.assertEqual(len(cycles), 0)

    def test_get_stats(self):
        """Test statistics generation"""
        a = Path("/project/a.py")
        b = Path("/project/b.py")
        c = Path("/project/c.py")

        self.graph.add_dependency(a, b)
        self.graph.add_dependency(a, c)
        self.graph.add_dependency(c, b)
        self.graph.add_external(a, "requests")

        stats = self.graph.get_stats()

        self.assertEqual(stats['total_files'], 3)
        self.assertEqual(stats['total_dependencies'], 3)
        self.assertEqual(stats['total_external'], 1)
        self.assertEqual(stats['cycles'], 0)

        # b is imported twice (by a and c)
        most_imported = stats['most_imported'][0] if stats['most_imported'] else None
        if most_imported:
            self.assertEqual(most_imported[0], b)
            self.assertEqual(most_imported[1], 2)

    def test_to_dict(self):
        """Test JSON serialization"""
        self.graph.root_path = Path("/project")
        a = Path("/project/a.py")
        b = Path("/project/b.py")

        self.graph.add_dependency(a, b)
        self.graph.add_external(a, "requests")

        result = self.graph.to_dict()

        # Check structure
        self.assertIn('nodes', result)
        self.assertIn('edges', result)
        self.assertIn('external', result)

        # Check nodes
        self.assertIn('a.py', result['nodes'])
        self.assertIn('b.py', result['nodes'])

        # Check edges
        self.assertEqual(len(result['edges']), 1)
        edge = result['edges'][0]
        self.assertEqual(edge['from'], 'a.py')
        self.assertEqual(edge['to'], 'b.py')

        # Check external
        self.assertIn('a.py', result['external'])
        self.assertEqual(result['external']['a.py'], ['requests'])


if __name__ == "__main__":
    unittest.main()