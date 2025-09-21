#!/usr/bin/env python
"""
FastDeps MCP Server - Simplified implementation following Serena's pattern
"""

import asyncio
import json
from pathlib import Path
from typing import Any

# Core imports
from .analyzer import DependencyAnalyzer
from .output import GraphRenderer

async def main():
    """Main MCP server entry point using stdio."""
    import sys

    # Check if MCP is available
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent
    except ImportError:
        print(json.dumps({
            "error": "MCP not installed. Install with: pip install fastdeps[mcp]"
        }), file=sys.stderr)
        sys.exit(1)

    # Create server
    server = Server("fastdeps")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available FastDeps tools."""
        return [
            Tool(
                name="analyze_dependencies",
                description="Analyze Python project dependencies",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to Python project",
                            "default": "."
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["json", "text", "dot"],
                            "default": "json"
                        },
                        "include_external": {
                            "type": "boolean",
                            "default": False
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="find_circular_deps",
                description="Find circular dependencies in project",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "default": "."
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_dependency_stats",
                description="Get statistics about project dependencies",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "default": "."
                        }
                    },
                    "required": []
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool execution."""

        try:
            if name == "analyze_dependencies":
                project_path = arguments.get("project_path", ".")
                output_format = arguments.get("output_format", "json")
                include_external = arguments.get("include_external", False)

                # Resolve to absolute path
                abs_path = Path(project_path).resolve()
                if not abs_path.exists():
                    return [TextContent(
                        type="text",
                        text=f"Error: Path does not exist: {project_path} (resolved to {abs_path})"
                    )]

                # Log for debugging
                import sys
                print(f"FastDeps MCP: Analyzing {abs_path} (internal_only={not include_external})",
                      file=sys.stderr, flush=True)

                # Run analysis
                analyzer = DependencyAnalyzer()
                graph = analyzer.analyze(
                    str(abs_path),
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

                return [TextContent(type="text", text=result)]

            elif name == "find_circular_deps":
                project_path = arguments.get("project_path", ".")

                # Resolve to absolute path
                abs_path = Path(project_path).resolve()
                if not abs_path.exists():
                    return [TextContent(
                        type="text",
                        text=f"Error: Path does not exist: {project_path} (resolved to {abs_path})"
                    )]

                # Run analysis
                analyzer = DependencyAnalyzer()
                graph = analyzer.analyze(str(abs_path), internal_only=True)

                # Find cycles
                cycles = graph.find_cycles()

                if not cycles:
                    result = "No circular dependencies found! ✨"
                else:
                    lines = [f"Found {len(cycles)} circular dependencies:"]
                    for i, cycle in enumerate(cycles, 1):
                        lines.append(f"\nCycle {i}:")
                        for file_path in cycle:
                            rel_path = file_path.relative_to(graph.root_path) if graph.root_path else file_path
                            lines.append(f"  → {rel_path}")
                    result = "\n".join(lines)

                return [TextContent(type="text", text=result)]

            elif name == "get_dependency_stats":
                project_path = arguments.get("project_path", ".")

                # Resolve to absolute path
                abs_path = Path(project_path).resolve()
                if not abs_path.exists():
                    return [TextContent(
                        type="text",
                        text=f"Error: Path does not exist: {project_path} (resolved to {abs_path})"
                    )]

                # Run analysis
                analyzer = DependencyAnalyzer()
                graph = analyzer.analyze(str(abs_path), internal_only=False)

                # Get stats
                stats = graph.get_stats()

                # Format as JSON
                result = json.dumps({
                    "total_files": stats['total_files'],
                    "total_dependencies": stats['total_dependencies'],
                    "external_dependencies": stats['total_external'],
                    "circular_dependencies": stats['cycles'],
                    "most_imported": [
                        str(path.relative_to(graph.root_path) if graph.root_path else path)
                        for path, _ in stats['most_imported'][:3]
                    ]
                }, indent=2)

                return [TextContent(type="text", text=result)]

            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())