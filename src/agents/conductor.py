"""
Conductor agent for the multi-agent system.
This agent orchestrates the workflow between coder, researcher, tester, and adversary agents.
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json


class AgentType(str, Enum):
    CODER = "coder"
    RESEARCHER = "researcher"
    TESTER = "tester"
    ADVERSARY = "adversary"


@dataclass
class AgentConfig:
    type: AgentType
    description: str
    # Add a method to create an instance of the agent
    def create_instance(self):
        # This would be implemented in a real system
        return None


class CommunicationMessage:
    """Message format for agent communication."""
    
    def __init__(self, sender: AgentType, receiver: AgentType, task: str, data: Any = None):
        self.sender = sender
        self.receiver = receiver
        self.task = task
        self.data = data
        self.timestamp = asyncio.get_event_loop().time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender.value,
            "receiver": self.receiver.value,
            "task": self.task,
            "data": self.data,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            AgentType(data["sender"]),
            AgentType(data["receiver"]),
            data["task"],
            data.get("data")
        )


class Conductor:
    """Main orchestrator for the multi-agent system."""
    
    def __init__(self):
        self.agents: Dict[AgentType, AgentConfig] = {
            AgentType.CODER: AgentConfig(AgentType.CODER, "Writes code for the system"),
            AgentType.RESEARCHER: AgentConfig(AgentType.RESEARCHER, "Conducts research for the system"),
            AgentType.TESTER: AgentConfig(AgentType.TESTER, "Writes tests for the system"),
            AgentType.ADVERSARY: AgentConfig(AgentType.ADVERSARY, "Challenges the system"),
        }
        self.current_cycle = 0
        self.history = []
        self._message_queue: List[CommunicationMessage] = []
    
    def _validate_task(self, task: str) -> bool:
        """Validate that the task is not empty or invalid."""
        return task is not None and isinstance(task, str) and len(task.strip()) > 0
    
    def _create_message(self, sender: AgentType, receiver: AgentType, task: str, data: Any = None) -> CommunicationMessage:
        """Create a communication message."""
        if not self._validate_task(task):
            raise ValueError("Invalid task provided")
        
        message = CommunicationMessage(sender, receiver, task, data)
        self._message_queue.append(message)
        return message
    
    async def _send_message(self, message: CommunicationMessage) -> Dict[str, Any]:
        """Send a message to an agent and return the response."""
        # In a real implementation, this would actually communicate with the agent
        # For now, we simulate the communication
        await asyncio.sleep(0.05)  # Simulate network delay
        
        return {
            "message": message.to_dict(),
            "status": "delivered",
            "timestamp": asyncio.get_event_loop().time()
        }
    
    async def start_cycle(self, task: str) -> Dict[str, Any]:
        """Start a new cycle with the given task."""
        if not self._validate_task(task):
            raise ValueError("Invalid task provided")
        
        self.current_cycle += 1
        cycle_result = {
            "cycle": self.current_cycle,
            "task": task,
            "status": "CONTINUE",
            "agents_involved": [],
            "results": {},
            "messages_sent": 0
        }
        
        # Add the task to history
        self.history.append(cycle_result)
        
        # Create communication plan for this cycle
        # In a real system, this would be more sophisticated
        messages = []
        for agent_type in self.agents.keys():
            # Create a message for each agent
            message = self._create_message(AgentType.CODER, agent_type, task)
            messages.append(message)
            cycle_result["messages_sent"] += 1
        
        # Simulate sending messages and receiving responses
        for message in messages:
            response = await self._send_message(message)
            cycle_result["agents_involved"].append(message.receiver)
            cycle_result["results"][message.receiver] = response
        
        return cycle_result
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Return the execution history."""
        return self.history
    
    async def run_multiple_cycles(self, tasks: List[str]) -> List[Dict[str, Any]]:
        """Run multiple cycles sequentially."""
        results = []
        for task in tasks:
            result = await self.start_cycle(task)
            results.append(result)
        return results
    
    def get_message_queue(self) -> List[Dict[str, Any]]:
        """Return the current message queue."""
        return [msg.to_dict() for msg in self._message_queue]
    
    def clear_message_queue(self):
        """Clear the message queue."""
        self._message_queue.clear()