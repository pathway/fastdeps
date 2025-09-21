"""Setup script for FastDeps"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text()
else:
    long_description = "FastDeps - Lightning-fast Python dependency analyzer"

setup(
    name="fastdeps",
    version="1.0.0",
    author="FastDeps Team",
    description="Lightning-fast Python dependency analyzer using AST parsing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/fastdeps",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[],  # No external dependencies!
    extras_require={
        "dev": ["pytest>=7.0", "black", "mypy"],
    },
    entry_points={
        "console_scripts": [
            "fastdeps=fastdeps.cli:main",
        ],
    },
)