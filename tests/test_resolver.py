"""Tests for module resolution"""

import tempfile
import unittest
from pathlib import Path

from fastdeps.resolver import ModuleResolver


class TestModuleResolver(unittest.TestCase):
    """Test import resolution to files"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self._create_project_structure()
        self.resolver = ModuleResolver(self.temp_dir)

    def _create_project_structure(self):
        """Create a test project structure"""
        # Root module
        (self.temp_dir / "main.py").touch()

        # Package with __init__
        pkg = self.temp_dir / "mypackage"
        pkg.mkdir()
        (pkg / "__init__.py").touch()
        (pkg / "module.py").touch()

        # Subpackage
        subpkg = pkg / "subpkg"
        subpkg.mkdir()
        (subpkg / "__init__.py").touch()
        (subpkg / "helper.py").touch()

        # Another top-level package
        utils = self.temp_dir / "utils"
        utils.mkdir()
        (utils / "__init__.py").touch()
        (utils / "common.py").touch()

    def test_resolve_simple_module(self):
        """Test resolving simple module in root"""
        result = self.resolver.resolve_import("main", self.temp_dir / "other.py")
        self.assertEqual(result, self.temp_dir / "main.py")

    def test_resolve_package(self):
        """Test resolving package __init__"""
        result = self.resolver.resolve_import("mypackage",
                                             self.temp_dir / "main.py")
        self.assertEqual(result, self.temp_dir / "mypackage" / "__init__.py")

    def test_resolve_package_module(self):
        """Test resolving module in package"""
        result = self.resolver.resolve_import("mypackage.module",
                                             self.temp_dir / "main.py")
        self.assertEqual(result, self.temp_dir / "mypackage" / "module.py")

    def test_resolve_subpackage(self):
        """Test resolving subpackage"""
        result = self.resolver.resolve_import("mypackage.subpkg",
                                             self.temp_dir / "main.py")
        self.assertEqual(result,
                        self.temp_dir / "mypackage" / "subpkg" / "__init__.py")

    def test_resolve_subpackage_module(self):
        """Test resolving module in subpackage"""
        result = self.resolver.resolve_import("mypackage.subpkg.helper",
                                             self.temp_dir / "main.py")
        self.assertEqual(result,
                        self.temp_dir / "mypackage" / "subpkg" / "helper.py")

    def test_resolve_stdlib(self):
        """Test stdlib modules return None"""
        result = self.resolver.resolve_import("os", self.temp_dir / "main.py")
        self.assertIsNone(result)

        result = self.resolver.resolve_import("os.path", self.temp_dir / "main.py")
        self.assertIsNone(result)

    def test_resolve_external(self):
        """Test external modules return None"""
        result = self.resolver.resolve_import("numpy", self.temp_dir / "main.py")
        self.assertIsNone(result)

    def test_resolve_relative_same_package(self):
        """Test relative import within same package"""
        # from . import module (from within mypackage)
        from_file = self.temp_dir / "mypackage" / "other.py"
        result = self.resolver.resolve_import("module", from_file, level=1)
        self.assertEqual(result, self.temp_dir / "mypackage" / "module.py")

    def test_resolve_relative_parent_package(self):
        """Test relative import from parent package"""
        # from .. import utils (from within mypackage/subpkg)
        from_file = self.temp_dir / "mypackage" / "subpkg" / "helper.py"
        result = self.resolver.resolve_import("", from_file, level=2)
        self.assertEqual(result, self.temp_dir / "mypackage" / "__init__.py")

    def test_resolve_relative_sibling(self):
        """Test relative import of sibling package"""
        # from ..utils import common (from within mypackage)
        from_file = self.temp_dir / "mypackage" / "module.py"
        result = self.resolver.resolve_import("utils.common", from_file, level=2)
        self.assertEqual(result, self.temp_dir / "utils" / "common.py")

    def test_is_external(self):
        """Test external module detection"""
        self.assertFalse(self.resolver.is_external("os"))  # stdlib
        self.assertFalse(self.resolver.is_external("main"))  # in project
        self.assertFalse(self.resolver.is_external("mypackage"))  # in project
        self.assertTrue(self.resolver.is_external("requests"))  # external
        self.assertTrue(self.resolver.is_external("numpy"))  # external


class TestModuleIndex(unittest.TestCase):
    """Test module indexing"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_index_building(self):
        """Test that file index is built correctly"""
        # Create structure
        (self.temp_dir / "app.py").touch()
        pkg = self.temp_dir / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").touch()
        (pkg / "mod.py").touch()

        resolver = ModuleResolver(self.temp_dir)

        # Check index contains expected modules
        self.assertIn("app", resolver.file_index)
        self.assertIn("pkg", resolver.file_index)  # __init__.py becomes just "pkg"
        self.assertIn("pkg.mod", resolver.file_index)

    def test_package_detection(self):
        """Test that packages are detected correctly"""
        # Package (has __init__.py)
        pkg = self.temp_dir / "package"
        pkg.mkdir()
        (pkg / "__init__.py").touch()

        # Non-package (no __init__.py)
        non_pkg = self.temp_dir / "notpackage"
        non_pkg.mkdir()
        (non_pkg / "module.py").touch()

        resolver = ModuleResolver(self.temp_dir)

        self.assertIn(pkg, resolver.package_dirs)
        self.assertNotIn(non_pkg, resolver.package_dirs)


if __name__ == "__main__":
    unittest.main()