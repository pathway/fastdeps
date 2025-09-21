#!/usr/bin/env python
"""MCP (Model Context Protocol) server for FastDeps"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, List, Dict, Optional

# MCP imports (will be available when mcp package is installed)
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Stub classes for when MCP isn't installed
    class Server:
        def __init__(self, name): pass
        def list_tools(self): return lambda f: f
        def call_tool(self): return lambda f: f

    class Tool:
        def __init__(self, **kwargs): pass

    class TextContent:
        def __init__(self, **kwargs): pass

# Import our core functionality
from .analyzer import DependencyAnalyzer
from .graph import DependencyGraph
from .output import GraphRenderer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
app = Server("fastdeps")

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available FastDeps MCP tools."""
    return [
        Tool(
            name="analyze_project",
            description="Analyze Python project dependencies comprehensively",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to Python project to analyze",
                        "default": "."
                    },
                    "include_external": {
                        "type": "boolean",
                        "description": "Include external dependencies in analysis",
                        "default": False
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["json", "text", "dot"],
                        "description": "Output format for results",
                        "default": "json"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="find_cycles",
            description="Find circular dependencies in Python project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to Python project",
                        "default": "."
                    },
                    "detailed": {
                        "type": "boolean",
                        "description": "Include detailed cycle paths",
                        "default": True
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="trace_imports",
            description="Trace import paths between two modules",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to Python project",
                        "default": "."
                    },
                    "from_module": {
                        "type": "string",
                        "description": "Source module path (e.g., 'src/main.py')"
                    },
                    "to_module": {
                        "type": "string",
                        "description": "Target module path (e.g., 'src/utils.py')"
                    }
                },
                "required": ["from_module", "to_module"]
            }
        ),
        Tool(
            name="get_stats",
            description="Get dependency statistics for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to Python project",
                        "default": "."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="check_module",
            description="Check dependencies for a specific Python module",
            inputSchema={
                "type": "object",
                "properties": {
                    "module_path": {
                        "type": "string",
                        "description": "Path to specific Python file"
                    },
                    "include_indirect": {
                        "type": "boolean",
                        "description": "Include indirect dependencies",
                        "default": False
                    }
                },
                "required": ["module_path"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle MCP tool calls."""

    try:
        if name == "analyze_project":
            return await analyze_project(arguments)
        elif name == "find_cycles":
            return await find_cycles(arguments)
        elif name == "trace_imports":
            return await trace_imports(arguments)
        elif name == "get_stats":
            return await get_stats(arguments)
        elif name == "check_module":
            return await check_module(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

async def analyze_project(args: Dict[str, Any]) -> List[TextContent]:
    """Analyze complete project dependencies."""
    project_path = args.get("project_path", ".")
    include_external = args.get("include_external", False)
    output_format = args.get("output_format", "json")

    # Run analysis
    analyzer = DependencyAnalyzer()
    graph = analyzer.analyze(
        project_path,
        internal_only=not include_external
    )

    # Format output
    renderer = GraphRenderer(graph)

    if output_format == "json":
        result = renderer.to_json()
    elif output_format == "text":
        result = renderer.to_text()
    elif output_format == "dot":
        result = renderer.to_dot(show_external=include_external)
    else:
        result = renderer.to_json()

    return [TextContent(
        type="text",
        text=result
    )]

async def find_cycles(args: Dict[str, Any]) -> List[TextContent]:
    """Find circular dependencies."""
    project_path = args.get("project_path", ".")
    detailed = args.get("detailed", True)

    # Run analysis
    analyzer = DependencyAnalyzer()
    graph = analyzer.analyze(project_path, internal_only=True)

    # Find cycles
    cycles = graph.find_cycles()

    if not cycles:
        return [TextContent(
            type="text",
            text="No circular dependencies found! ✨"
        )]

    # Format results
    result = [f"Found {len(cycles)} circular dependencies:\n"]

    for i, cycle in enumerate(cycles, 1):
        result.append(f"\nCycle {i}:")
        if detailed:
            for file_path in cycle:
                rel_path = file_path.relative_to(graph.root_path) if graph.root_path else file_path
                result.append(f"  → {rel_path}")
        else:
            result.append(f"  {len(cycle)} modules involved")

    return [TextContent(
        type="text",
        text="\n".join(result)
    )]

async def trace_imports(args: Dict[str, Any]) -> List[TextContent]:
    """Trace import path between modules."""
    project_path = args.get("project_path", ".")
    from_module = args.get("from_module")
    to_module = args.get("to_module")

    if not from_module or not to_module:
        return [TextContent(
            type="text",
            text="Error: both from_module and to_module are required"
        )]

    # Convert to absolute paths
    project_root = Path(project_path).resolve()
    from_path = project_root / from_module
    to_path = project_root / to_module

    # Run analysis
    analyzer = DependencyAnalyzer()
    graph = analyzer.analyze(project_path, internal_only=True)

    # Check if modules exist in graph
    if from_path not in graph.nodes:
        return [TextContent(
            type="text",
            text=f"Module not found: {from_module}"
        )]

    if to_path not in graph.nodes:
        return [TextContent(
            type="text",
            text=f"Module not found: {to_module}"
        )]

    # Check direct dependency
    if to_path in graph.nodes[from_path].imports:
        return [TextContent(
            type="text",
            text=f"✅ Direct import: {from_module} → {to_module}"
        )]

    # Find indirect paths using BFS
    from collections import deque

    visited = set()
    queue = deque([(from_path, [from_path])])
    paths = []

    while queue and len(paths) < 5:  # Limit to 5 paths
        current, path = queue.popleft()

        if current in visited:
            continue
        visited.add(current)

        if current in graph.nodes:
            for imported in graph.nodes[current].imports:
                new_path = path + [imported]

                if imported == to_path:
                    paths.append(new_path)
                elif imported not in visited:
                    queue.append((imported, new_path))

    if not paths:
        return [TextContent(
            type="text",
            text=f"❌ No import path found from {from_module} to {to_module}"
        )]

    # Format paths
    result = [f"Found {len(paths)} import path(s):\n"]

    for i, path in enumerate(paths, 1):
        result.append(f"\nPath {i} ({len(path)-1} hop(s)):")
        for j, module in enumerate(path):
            rel_path = module.relative_to(project_root)
            prefix = "  " + ("→ " if j > 0 else "")
            result.append(f"{prefix}{rel_path}")

    return [TextContent(
        type="text",
        text="\n".join(result)
    )]

async def get_stats(args: Dict[str, Any]) -> List[TextContent]:
    """Get project dependency statistics."""
    project_path = args.get("project_path", ".")

    # Run analysis
    analyzer = DependencyAnalyzer()
    graph = analyzer.analyze(project_path, internal_only=False)

    # Get stats
    stats = graph.get_stats()

    # Format as JSON for structured data
    result = {
        "summary": {
            "total_files": stats['total_files'],
            "total_dependencies": stats['total_dependencies'],
            "external_dependencies": stats['total_external'],
            "circular_dependencies": stats['cycles']
        },
        "most_imported": [
            {
                "file": str(path.relative_to(graph.root_path) if graph.root_path else path),
                "import_count": count
            }
            for path, count in stats['most_imported']
        ],
        "most_imports": [
            {
                "file": str(path.relative_to(graph.root_path) if graph.root_path else path),
                "import_count": count
            }
            for path, count in stats['most_imports']
        ]
    }

    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]

async def check_module(args: Dict[str, Any]) -> List[TextContent]:
    """Check dependencies for specific module."""
    module_path = args.get("module_path")
    include_indirect = args.get("include_indirect", False)

    if not module_path:
        return [TextContent(
            type="text",
            text="Error: module_path is required"
        )]

    # Get absolute path
    module_file = Path(module_path).resolve()

    if not module_file.exists():
        return [TextContent(
            type="text",
            text=f"Module not found: {module_path}"
        )]

    # Analyze just this file
    from .parser import ImportExtractor

    extractor = ImportExtractor()
    imports = extractor.extract_imports(module_file)

    # Format results
    result = [f"Dependencies for {module_path}:\n"]
    result.append(f"Total imports: {len(imports)}\n")

    # Group by type
    absolute_imports = [i for i in imports if i.level == 0]
    relative_imports = [i for i in imports if i.level > 0]

    if absolute_imports:
        result.append("\nAbsolute imports:")
        for imp in absolute_imports:
            if imp.names:
                result.append(f"  from {imp.module} import {', '.join(imp.names)}")
            else:
                result.append(f"  import {imp.module}")

    if relative_imports:
        result.append("\nRelative imports:")
        for imp in relative_imports:
            dots = "." * imp.level
            if imp.module:
                result.append(f"  from {dots}{imp.module} import {', '.join(imp.names)}")
            else:
                result.append(f"  from {dots} import {', '.join(imp.names)}")

    return [TextContent(
        type="text",
        text="\n".join(result)
    )]

async def main():
    """Main entry point for MCP server mode."""
    if not MCP_AVAILABLE:
        print("Error: MCP package not installed. Install with: pip install mcp",
              file=sys.stderr)
        sys.exit(1)

    logger.info("Starting FastDeps MCP server...")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

def serve_command():
    """Entry point for 'fastdeps serve' command."""
    asyncio.run(main())

if __name__ == "__main__":
    serve_command()