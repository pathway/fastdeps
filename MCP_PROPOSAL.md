# FastDeps MCP Server Integration Proposal

## Overview

Add Model Context Protocol (MCP) server capabilities to FastDeps, allowing AI assistants to analyze Python dependencies programmatically.

## Dual-Mode Operation

FastDeps will support two modes:

### 1. CLI Mode (Current)
```bash
fastdeps myproject                    # Direct terminal usage
fastdeps myproject -o graph.png       # Generate visualizations
```

### 2. MCP Server Mode (New)
```bash
fastdeps serve                         # Start MCP server
uvx --from fastdeps fastdeps serve    # Via uvx
```

## MCP Tools Interface

### Tool 1: analyze_project
Comprehensive project dependency analysis.

**Input Schema:**
```json
{
  "project_path": "string",           // Path to analyze
  "include_external": "boolean",      // Include external deps
  "max_depth": "integer"              // Max recursion depth
}
```

**Returns:**
- File count and structure
- Dependency graph
- Import statistics
- Circular dependency warnings

### Tool 2: find_cycles
Detect and analyze circular dependencies.

**Input Schema:**
```json
{
  "project_path": "string",
  "detailed": "boolean"               // Include full cycle paths
}
```

**Returns:**
- List of circular dependency chains
- Severity assessment
- Suggested fixes

### Tool 3: trace_imports
Trace import paths between modules.

**Input Schema:**
```json
{
  "project_path": "string",
  "from_module": "string",            // Source module
  "to_module": "string",              // Target module
  "show_all_paths": "boolean"         // Show all possible paths
}
```

**Returns:**
- Import chain(s) from source to target
- Direct vs indirect dependencies
- Path length and complexity

### Tool 4: compare_dependencies
Compare dependencies between projects or versions.

**Input Schema:**
```json
{
  "project_a": "string",              // First project path
  "project_b": "string",              // Second project path
  "show_diff_only": "boolean"         // Only show differences
}
```

**Returns:**
- Common dependencies
- Unique to each project
- Version differences
- Structural changes

### Tool 5: suggest_refactoring
AI-powered dependency improvement suggestions.

**Input Schema:**
```json
{
  "project_path": "string",
  "focus_area": "string"              // "cycles"|"complexity"|"external"
}
```

**Returns:**
- Identified issues
- Refactoring suggestions
- Priority rankings
- Impact assessment

## Implementation Structure

```
fastdeps/
├── fastdeps/
│   ├── __init__.py
│   ├── cli.py                 # Existing CLI
│   ├── mcp_server.py          # New MCP server
│   ├── tools/                 # MCP tool implementations
│   │   ├── __init__.py
│   │   ├── analyze.py
│   │   ├── cycles.py
│   │   ├── trace.py
│   │   ├── compare.py
│   │   └── suggest.py
│   └── core/                  # Shared logic
│       ├── parser.py
│       ├── resolver.py
│       └── graph.py
```

## Configuration

### MCP Server Config (mcp.json)
```json
{
  "name": "fastdeps",
  "version": "1.1.0",
  "description": "Python dependency analysis MCP server",
  "tools": [
    "analyze_project",
    "find_cycles",
    "trace_imports",
    "compare_dependencies",
    "suggest_refactoring"
  ],
  "configuration": {
    "max_file_size": 10485760,
    "timeout": 30,
    "cache_enabled": true
  }
}
```

## Usage Examples

### For AI Assistants
```python
# In Claude or other MCP-enabled assistant
result = use_tool("analyze_project", {
    "project_path": "/path/to/project",
    "include_external": true
})

cycles = use_tool("find_cycles", {
    "project_path": "/path/to/project",
    "detailed": true
})
```

### For Developers
```bash
# Start MCP server
fastdeps serve --port 3000

# Or with uvx
uvx --from fastdeps fastdeps serve

# Test with MCP client
mcp-client localhost:3000 analyze_project '{"project_path": "."}'
```

## Benefits

### For AI Assistants
- Direct access to dependency analysis
- Structured data for reasoning
- Real-time project analysis
- Integration with development workflows

### For Developers
- Automated dependency audits
- CI/CD integration via MCP
- IDE plugin potential
- Scriptable analysis

## Implementation Timeline

1. **Phase 1**: Basic MCP server with analyze_project tool
2. **Phase 2**: Add cycles and trace tools
3. **Phase 3**: Implement compare and suggest tools
4. **Phase 4**: Optimization and caching
5. **Phase 5**: Documentation and examples

## Backwards Compatibility

- Existing CLI remains unchanged
- All current features preserved
- New `serve` subcommand for MCP mode
- Same core analysis engine

## Testing Strategy

- Unit tests for each MCP tool
- Integration tests with MCP protocol
- Performance benchmarks
- Real-world project testing
- AI assistant integration testing

## Security Considerations

- Read-only file system access
- Configurable timeout limits
- Path traversal protection
- Resource usage limits
- No code execution

## Future Enhancements

- **Streaming results** for large projects
- **Incremental analysis** with file watching
- **Caching layer** for repeated queries
- **Webhook support** for CI/CD
- **Multi-project workspaces**
- **Language model integration** for suggestions

## Example MCP Interaction

```
User: "Analyze the dependencies of my Django project"

Assistant uses MCP:
→ analyze_project(project_path="/home/user/django-app")

Returns structured data:
{
  "summary": {
    "total_files": 234,
    "internal_deps": 567,
    "external_deps": 45,
    "cycles": 3
  },
  "critical_issues": [
    "Circular dependency: models.py ↔ views.py ↔ serializers.py"
  ],
  "suggestions": [
    "Consider extracting shared logic to utils module"
  ]
}