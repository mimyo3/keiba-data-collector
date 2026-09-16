#!/usr/bin/env python3
"""
Main entry point for the multi-agent system.
This file demonstrates the conductor's ability to run multiple cycles.
"""

import asyncio
from src.agents.conductor import Conductor

async def main():
    # Create the conductor
    conductor = Conductor()
    
    # Define tasks for multiple cycles
    tasks = [
        "Implement initial agent framework",
        "Create agent communication protocol",
        "Add error handling and logging",
        "Test multi-agent coordination",
        "Optimize performance"
    ]
    
    print("Starting multi-agent system with conductor...")
    
    # Run multiple cycles
    results = await conductor.run_multiple_cycles(tasks)
    
    # Display results
    print(f"\nCompleted {len(results)} cycles:")
    for result in results:
        print(f"  Cycle {result['cycle']}: {result['task']}")
        print(f"    Status: {result['status']}")
        print(f"    Agents involved: {', '.join([str(agent) for agent in result['agents_involved']])}")
        print()

if __name__ == "__main__":
    asyncio.run(main())