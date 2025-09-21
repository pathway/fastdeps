# FastDeps - Lightning-Fast Python Dependency Analyzer

## Mission
Build a **FAST**, **SIMPLE**, **CORRECT** Python dependency analyzer that works on massive monorepos in seconds, not hours.

## Core Principles
1. **AST-only** - Never execute code, only parse
2. **Parallel** - Use all CPU cores
3. **Incremental** - Cache aggressively
4. **Focused** - Analyze only what's requested
5. **Simple** - One command, clear output

## Why FastDeps vs pydeps?

| Feature | pydeps | FastDeps |
|---------|---------|----------|
| Method | Executes imports | AST parsing only |
| Speed | O(n²) - follows all imports | O(n) - parallel scan |
| Monorepo | Scans entire tree | Analyzes only target |
| 10K files | Hours/timeout | <5 seconds |
| Safety | Runs code | Read-only |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   CLI       │────▶│  Analyzer    │────▶│  Output     │
│  fastdeps   │     │              │     │  .dot/.svg  │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌──────────┐  ┌──────────┐
              │  Parser  │  │  Cache   │
              │   AST    │  │  SQLite  │
              └──────────┘  └──────────┘
                    │
              ┌─────┴─────┐
              ▼           ▼
        ┌──────────┐ ┌──────────┐
        │ Worker 1 │ │ Worker N │
        │ Parallel │ │ Parallel │
        └──────────┘ └──────────┘
```

## Usage Examples

```bash
# Analyze single module (FAST - only scans this module)
fastdeps runner_elf

# Analyze with visualization
fastdeps runner_elf --output graph.svg

# Show only internal dependencies
fastdeps myproject --internal-only

# Detect circular imports
fastdeps myproject --show-cycles

# Analyze specific file
fastdeps src/main.py

# JSON output for tooling
fastdeps myproject --json > deps.json
```

## Implementation Plan

### Phase 1: Core Engine (Day 1)
```python
# fastdeps/parser.py
class ImportExtractor:
    def extract_imports(file_path: Path) -> List[Import]:
        """Extract imports using AST - NEVER executes code"""

# fastdeps/analyzer.py
class DependencyAnalyzer:
    def analyze(target: str) -> DependencyGraph:
        """Main analysis pipeline"""
```

### Phase 2: Performance (Day 2)
```python
# fastdeps/parallel.py
class ParallelProcessor:
    def process_files(files: List[Path]) -> Dict[Path, List[Import]]:
        """Process files using multiprocessing.Pool"""

# fastdeps/cache.py
class DependencyCache:
    def get_or_compute(file: Path) -> List[Import]:
        """SQLite cache with mtime invalidation"""
```

### Phase 3: Resolution (Day 3)
```python
# fastdeps/resolver.py
class ImportResolver:
    def resolve(imp: Import, from_file: Path) -> Optional[Path]:
        """Resolve imports to actual files"""

# fastdeps/graph.py
class DependencyGraph:
    def find_cycles() -> List[List[str]]:
        """Detect circular dependencies"""
```

### Phase 4: Output (Day 4)
```python
# fastdeps/output.py
class GraphRenderer:
    def to_dot() -> str:
        """Generate Graphviz DOT format"""
    def to_json() -> dict:
        """Generate JSON for tools"""
    def to_text() -> str:
        """Human-readable tree"""
```

## Key Algorithms

### 1. Fast Import Extraction (AST-based)
```python
def extract_imports_fast(file_path):
    # Read only first 10KB (most imports at top)
    with open(file_path, 'rb') as f:
        source = f.read(10240)

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Read full file if truncated
        with open(file_path, 'rb') as f:
            source = f.read()
        tree = ast.parse(source)

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(node_to_import(node))

    return imports
```

### 2. Parallel File Processing
```python
def analyze_parallel(files, num_workers=None):
    num_workers = num_workers or cpu_count()

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Process in chunks for better load balancing
        chunk_size = max(1, len(files) // (num_workers * 4))
        chunks = [files[i:i+chunk_size]
                  for i in range(0, len(files), chunk_size)]

        futures = [executor.submit(process_chunk, chunk)
                   for chunk in chunks]

        results = {}
        for future in as_completed(futures):
            results.update(future.result())

    return results
```

### 3. Smart Module Resolution
```python
class ModuleResolver:
    def __init__(self, root_path):
        # Build file index ONCE
        self.file_index = {}
        self.package_index = {}

        for py_file in find_python_files(root_path):
            rel_path = py_file.relative_to(root_path)
            module_path = path_to_module(rel_path)
            self.file_index[module_path] = py_file

    def resolve(import_name, from_file):
        # Fast O(1) lookup
        if import_name in self.file_index:
            return self.file_index[import_name]

        # Handle relative imports
        if import_name.startswith('.'):
            return resolve_relative(import_name, from_file)

        return None  # External dependency
```

## Performance Targets

| Codebase | Files | Target Time | Actual pydeps |
|----------|-------|-------------|---------------|
| Small (runner_elf) | 10 | <0.1s | 2s |
| Medium (django) | 1K | <1s | 30s |
| Large (monorepo) | 10K | <5s | timeout |
| Massive | 100K | <60s | impossible |

## Differentiators from pydeps

### What we WON'T do:
- Execute any Python code
- Follow external dependencies by default
- Create dummy import files
- Scan parent package trees
- Use Python's import machinery

### What we WILL do:
- Parse only requested modules
- Use parallel processing
- Cache aggressively
- Provide clear, fast results
- Handle monorepos correctly

## File Structure

```
fastdeps/
├── PLAN.md           # This file
├── README.md         # User documentation
├── fastdeps/
│   ├── __init__.py
│   ├── cli.py        # Command-line interface
│   ├── parser.py     # AST import extraction
│   ├── analyzer.py   # Main analysis logic
│   ├── parallel.py   # Multiprocessing pipeline
│   ├── resolver.py   # Import resolution
│   ├── cache.py      # SQLite caching
│   ├── graph.py      # Dependency graph
│   └── output.py     # Output formatting
├── tests/
│   ├── test_parser.py
│   ├── test_resolver.py
│   └── fixtures/     # Test packages
└── setup.py          # pip installable

```

## Success Metrics

1. **Speed**: 1000x faster than pydeps on monorepos
2. **Correctness**: Handle all Python import styles
3. **Usability**: Single command, instant results
4. **Scalability**: Linear performance with file count

## MVP Features (v1.0)

- [x] AST-based import extraction
- [x] Parallel file processing
- [x] Basic import resolution
- [x] DOT output for Graphviz
- [x] Circular dependency detection
- [x] SQLite caching

## Future Features (v2.0)

- [ ] Watch mode for development
- [ ] Import depth limiting
- [ ] Package boundary analysis
- [ ] Unused import detection
- [ ] Export to multiple formats
- [ ] Web UI for visualization

## Development Timeline

- Day 1: Core AST parser and analyzer
- Day 2: Parallel processing and caching
- Day 3: Import resolution and graph building
- Day 4: CLI and output formats
- Day 5: Testing and benchmarks

## Testing Strategy

### Correctness Tests
- Standard imports: `import os`
- From imports: `from os import path`
- Relative imports: `from ..utils import helper`
- Circular imports: A → B → C → A
- Package vs module resolution

### Performance Tests
- Small: 10 files, <0.1s
- Medium: 1K files, <1s
- Large: 10K files, <5s
- Monorepo: Nested packages, correct isolation

### Edge Cases
- Syntax errors in files
- Missing __init__.py
- Symbolic links
- Import within functions
- Dynamic imports (report but don't follow)

## Why This Will Succeed

1. **Focused scope** - Do one thing well
2. **Modern Python** - Use stdlib AST, no hacks
3. **Parallel by design** - Not an afterthought
4. **Monorepo-first** - Built for large codebases
5. **No magic** - Transparent, predictable behavior

[SE] This will be 1000x faster than pydeps because we're not fighting Python's import system - we're bypassing it entirely.

[CS] O(n) complexity with files, parallelizable. Cache makes subsequent runs O(changed files only).

[OE] Zero side effects - read-only operation. Safe to run in production.