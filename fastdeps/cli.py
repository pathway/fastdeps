#!/usr/bin/env python
"""Command-line interface for FastDeps"""

import argparse
import sys
import json
from pathlib import Path

from .analyzer import DependencyAnalyzer
from .output import GraphRenderer


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="FastDeps - Lightning-fast Python dependency analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fastdeps mypackage                    # Analyze package
  fastdeps mypackage -o graph.png       # Generate PNG visualization
  fastdeps mypackage --show             # Analyze and display PNG
  fastdeps src/main.py                  # Analyze single file
  fastdeps myproject --internal-only    # Skip external dependencies
  fastdeps myproject --show-cycles      # Focus on circular dependencies
  fastdeps myproject --json             # Output JSON for tooling
        """
    )

    parser.add_argument(
        'target',
        help='File, directory, or package to analyze'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file (.dot, .png, .svg, .json, .txt)'
    )

    parser.add_argument(
        '--show',
        action='store_true',
        help='Display PNG after generation (requires -o with .png)'
    )

    parser.add_argument(
        '--internal-only',
        action='store_true',
        help='Only show internal project dependencies'
    )

    parser.add_argument(
        '--show-external',
        action='store_true',
        help='Include external dependencies in visualization'
    )

    parser.add_argument(
        '--show-cycles',
        action='store_true',
        help='Only show circular dependencies'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output JSON to stdout'
    )

    parser.add_argument(
        '--workers',
        type=int,
        help='Number of parallel workers (default: CPU count)'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )

    args = parser.parse_args()

    # Redirect print statements if quiet
    if args.quiet:
        import os
        sys.stdout = open(os.devnull, 'w')

    try:
        # Run analysis
        analyzer = DependencyAnalyzer(num_workers=args.workers)
        graph = analyzer.analyze(args.target, internal_only=args.internal_only)

        # Restore stdout for output
        if args.quiet:
            sys.stdout = sys.__stdout__

        # Create renderer
        renderer = GraphRenderer(graph)

        # Handle different output modes
        if args.show_cycles:
            # Show only cycles
            cycles = graph.find_cycles()
            if cycles:
                print("Circular dependencies found:")
                for i, cycle in enumerate(cycles, 1):
                    print(f"\nCycle {i}:")
                    for file_path in cycle:
                        rel_path = file_path.relative_to(graph.root_path) if graph.root_path else file_path
                        print(f"  → {rel_path}")
            else:
                print("No circular dependencies found! ✨")
            return 0

        if args.json:
            # Output JSON to stdout
            print(renderer.to_json())
            return 0

        if args.output:
            # Save to file based on extension
            output_path = Path(args.output)
            ext = output_path.suffix.lower()

            if ext == '.dot':
                renderer.save_dot(output_path, show_external=args.show_external)
            elif ext == '.png':
                success = renderer.save_png(output_path,
                                           show_external=args.show_external,
                                           show=args.show)
                if not success:
                    return 1
            elif ext == '.svg':
                success = renderer.save_svg(output_path,
                                          show_external=args.show_external)
                if not success:
                    return 1
            elif ext == '.json':
                output_path.write_text(renderer.to_json())
                print(f"Saved JSON to {output_path}")
            elif ext == '.txt':
                output_path.write_text(renderer.to_text())
                print(f"Saved report to {output_path}")
            else:
                print(f"Unknown output format: {ext}")
                print("Supported: .dot, .png, .svg, .json, .txt")
                return 1
        else:
            # Default: print text report
            print(renderer.to_text())

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if not args.quiet:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())