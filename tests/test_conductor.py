import unittest
import asyncio
from unittest.mock import patch
from src.agents.conductor import Conductor


class TestConductor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.conductor = Conductor()

    def test_initial_cycle_value(self):
        """Test that the initial cycle value is 0."""
        self.assertEqual(self.conductor.current_cycle, 0)

    def test_cycle_increment_after_execute(self):
        """Test that current_cycle increments by 1 after calling start_cycle once."""
        # Run one cycle
        asyncio.run(self.conductor.start_cycle("test task"))
        
        # Check that cycle count is now 1
        self.assertEqual(self.conductor.current_cycle, 1)

    def test_cycle_increment_after_multiple_execute(self):
        """Test that current_cycle increments correctly for multiple calls."""
        # Run multiple cycles
        asyncio.run(self.conductor.start_cycle("test task 1"))
        asyncio.run(self.conductor.start_cycle("test task 2"))
        asyncio.run(self.conductor.start_cycle("test task 3"))

        # Check that cycle count is now 3
        self.assertEqual(self.conductor.current_cycle, 3)

    def test_cycle_reset(self):
        """Test that cycle count resets when conductor is reinitialized."""
        # Run one cycle
        asyncio.run(self.conductor.start_cycle("test task"))
        
        # Create a new conductor instance
        new_conductor = Conductor()
        
        # Check that the new conductor's cycle count is 0
        self.assertEqual(new_conductor.current_cycle, 0)


if __name__ == '__main__':
    unittest.main()
