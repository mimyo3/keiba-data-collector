"""
Agent base classes for the multi-agent system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class Agent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, task: str) -> Dict[str, Any]:
        """Execute a task and return results."""
        pass


class ConductorAgent(Agent):
    """Base class for conductor agents."""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
    
    async def execute(self, task: str) -> Dict[str, Any]:
        """Execute the task with conductor logic."""
        # This will be overridden by specific conductor implementations
        return {
            "agent": self.name,
            "task": task,
            "status": "executed",
            "result": "Base conductor execution"
        }


class AgentRegistry:
    """Registry for managing agent instances."""
    
    def __init__(self):
        self._agents = {}
    
    def register_agent(self, agent_type: str, agent_instance):
        """Register an agent instance."""
        self._agents[agent_type] = agent_instance
    
    def get_agent(self, agent_type: str):
        """Get an agent instance by type."""
        return self._agents.get(agent_type)
    
    def get_all_agents(self):
        """Get all registered agents."""
        return self._agents.copy()