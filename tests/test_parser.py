"""Tests for AST-based import parser"""

import tempfile
import unittest
from pathlib import Path

from fastdeps.parser import ImportExtractor, Import, find_python_files


class TestImportExtractor(unittest.TestCase):
    """Test import extraction"""

    def setUp(self):
        self.extractor = ImportExtractor()
        self.temp_dir = tempfile.mkdtemp()

    def _create_file(self, content: str, name: str = "test.py") -> Path:
        """Helper to create test Python file"""
        file_path = Path(self.temp_dir) / name
        file_path.write_text(content)
        return file_path

    def test_simple_import(self):
        """Test: import os"""
        file_path = self._create_file("import os\n")
        imports = self.extractor.extract_imports(file_path)

        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].module, "os")
        self.assertEqual(imports[0].names, [])
        self.assertEqual(imports[0].level, 0)
        self.assertEqual(imports[0].is_from, False)

    def test_multiple_imports(self):
        """Test: import os, sys"""
        file_path = self._create_file("import os, sys\n")
        imports = self.extractor.extract_imports(file_path)

        self.assertEqual(len(imports), 2)
        modules = [imp.module for imp in imports]
        self.assertIn("os", modules)
        self.assertIn("sys", modules)

    def test_from_import(self):
        """Test: from os import path"""
        file_path = self._create_file("from os import path\n")
        imports = self.extractor.extract_imports(file_path)

        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].module, "os")
        self.assertEqual(imports[0].names, ["path"])
        self.assertEqual(imports[0].is_from, True)

    def test_from_import_multiple(self):
        """Test: from os import path, environ"""
        file_path = self._create_file("from os import path, environ\n")
        imports = self.extractor.extract_imports(file_path)

        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].module, "os")
        self.assertEqual(set(imports[0].names), {"path", "environ"})

    def test_from_import_star(self):
        """Test: from os import *"""
        file_path = self._create_file("from os import *\n")
        imports = self.extractor.extract_imports(file_path)

        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].module, "os")
        self.assertEqual(imports[0].names, ["*"])

    def test_relative_import_single_dot(self):
        """Test: from . import utils"""
        file_path = self._create_file("from . import utils\n")
        imports = self.extractor.extract_imports(file_path)

        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].module, "")
        self.assertEqual(imports[0].names, ["utils"])
        self.assertEqual(imports[0].level, 1)

    def test_relative_import_double_dot(self):
        """Test: from ..package import module"""
        file_path = self._create_file("from ..package import module\n")
        imports = self.extractor.extract_imports(file_path)

        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].module, "package")
        self.assertEqual(imports[0].names, ["module"])
        self.assertEqual(imports[0].level, 2)

    def test_nested_import(self):
        """Test: from os.path import join"""
        file_path = self._create_file("from os.path import join\n")
        imports = self.extractor.extract_imports(file_path)

        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].module, "os.path")
        self.assertEqual(imports[0].names, ["join"])

    def test_import_in_function(self):
        """Test imports inside functions are detected"""
        content = """
def my_func():
    import json
    from datetime import datetime
    return json.dumps({})
"""
        file_path = self._create_file(content)
        imports = self.extractor.extract_imports(file_path)

        self.assertEqual(len(imports), 2)
        modules = [imp.module for imp in imports]
        self.assertIn("json", modules)
        self.assertIn("datetime", modules)

    def test_syntax_error_handling(self):
        """Test file with syntax errors returns empty"""
        file_path = self._create_file("import os\nthis is not valid python!")
        imports = self.extractor.extract_imports(file_path)

        self.assertEqual(imports, [])

    def test_empty_file(self):
        """Test empty file returns empty imports"""
        file_path = self._create_file("")
        imports = self.extractor.extract_imports(file_path)

        self.assertEqual(imports, [])

    def test_comments_and_strings(self):
        """Test imports in comments/strings are ignored"""
        content = '''
# import fake1
"""
import fake2
"""
import real
'''
        file_path = self._create_file(content)
        imports = self.extractor.extract_imports(file_path)

        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].module, "real")

    def test_line_numbers(self):
        """Test line numbers are tracked correctly"""
        content = """
import os

import sys

from json import loads
"""
        file_path = self._create_file(content)
        imports = self.extractor.extract_imports(file_path)

        # Find each import by module
        os_import = next(i for i in imports if i.module == "os")
        sys_import = next(i for i in imports if i.module == "sys")
        json_import = next(i for i in imports if i.module == "json")

        self.assertEqual(os_import.line, 2)
        self.assertEqual(sys_import.line, 4)
        self.assertEqual(json_import.line, 6)


class TestFindPythonFiles(unittest.TestCase):
    """Test Python file discovery"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_find_simple(self):
        """Test finding Python files in flat directory"""
        (self.temp_dir / "a.py").touch()
        (self.temp_dir / "b.py").touch()
        (self.temp_dir / "c.txt").touch()  # Not Python

        files = find_python_files(self.temp_dir)
        py_files = [f.name for f in files]

        self.assertEqual(len(files), 2)
        self.assertIn("a.py", py_files)
        self.assertIn("b.py", py_files)

    def test_find_nested(self):
        """Test finding Python files in nested directories"""
        (self.temp_dir / "main.py").touch()
        sub_dir = self.temp_dir / "sub"
        sub_dir.mkdir()
        (sub_dir / "module.py").touch()

        files = find_python_files(self.temp_dir)

        self.assertEqual(len(files), 2)

    def test_exclude_directories(self):
        """Test excluding __pycache__ and .git"""
        (self.temp_dir / "main.py").touch()

        # Create excluded directories
        cache_dir = self.temp_dir / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "cached.py").touch()

        git_dir = self.temp_dir / ".git"
        git_dir.mkdir()
        (git_dir / "config.py").touch()

        files = find_python_files(self.temp_dir)

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "main.py")

    def test_exclude_venv(self):
        """Test excluding virtual environment directories"""
        (self.temp_dir / "app.py").touch()

        venv_dir = self.temp_dir / "venv"
        venv_dir.mkdir()
        (venv_dir / "lib.py").touch()

        files = find_python_files(self.temp_dir)

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "app.py")


if __name__ == "__main__":
    unittest.main()