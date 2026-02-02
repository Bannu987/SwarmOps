"""
Memory System - Simple JSON-based memory for agents
Stores and retrieves information across sessions
"""

import json
import os
from datetime import datetime

class MemorySystem:
    """
    Simple memory system using JSON files
    Allows agents to remember information
    """
    
    def __init__(self, memory_file="memory.json"):
        """
        Initialize the memory system
        
        Args:
            memory_file (str): Path to the JSON file for storage
        """
        self.memory_file = memory_file
        self.memory = self._load_memory()
        print(f"💾 Memory System initialized")
        print(f"📁 Memory file: {self.memory_file}")
    
    def _load_memory(self):
        """Load memory from JSON file, create if doesn't exist"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    memory = json.load(f)
                    print(f"✅ Loaded existing memory ({len(memory)} items)")
                    return memory
            except json.JSONDecodeError:
                print("⚠️ Memory file corrupted, creating new one")
                return self._create_default_memory()
        else:
            print("📝 No existing memory found, creating new one")
            return self._create_default_memory()
    
    def _create_default_memory(self):
        """Create default memory structure"""
        return {
            "brand": {
                "voice": "friendly and professional",
                "colors": [],
                "target_audience": ""
            },
            "budget": {
                "monthly": 0,
                "spent": 0,
                "remaining": 0
            },
            "past_tasks": [],
            "preferences": {},
            "notes": []
        }
    
    def _save_memory(self):
        """Save memory to JSON file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving memory: {e}")
            return False
    
    def store(self, key, value, category=None):
        """
        Store a value in memory
        
        Args:
            key (str): The key to store under
            value: The value to store (any JSON-serializable type)
            category (str): Optional category (e.g., 'brand', 'budget')
        
        Returns:
            bool: Success status
        """
        try:
            if category and category in self.memory:
                self.memory[category][key] = value
                print(f"💾 Stored: {category}.{key} = {value}")
            else:
                self.memory[key] = value
                print(f"💾 Stored: {key} = {value}")
            
            self._save_memory()
            return True
        except Exception as e:
            print(f"❌ Error storing: {e}")
            return False
    
    def retrieve(self, key, category=None):
        """
        Retrieve a value from memory
        
        Args:
            key (str): The key to retrieve
            category (str): Optional category
            
        Returns:
            The stored value, or None if not found
        """
        try:
            if category and category in self.memory:
                value = self.memory[category].get(key)
                if value:
                    print(f"📖 Retrieved: {category}.{key} = {value}")
                return value
            else:
                value = self.memory.get(key)
                if value:
                    print(f"📖 Retrieved: {key} = {value}")
                return value
        except Exception as e:
            print(f"❌ Error retrieving: {e}")
            return None
    
    def log_task(self, task_description, result_summary, agent_used):
        """
        Log a completed task to memory
        
        Args:
            task_description (str): What was the task
            result_summary (str): Brief summary of result
            agent_used (str): Which agent completed it
        """
        task_record = {
            "timestamp": datetime.now().isoformat(),
            "task": task_description,
            "result": result_summary,
            "agent": agent_used
        }
        
        self.memory["past_tasks"].append(task_record)
        print(f"📝 Task logged: {task_description[:50]}...")
        self._save_memory()
    
    def get_recent_tasks(self, count=5):
        """
        Get recent tasks from memory
        
        Args:
            count (int): Number of recent tasks to retrieve
            
        Returns:
            list: Recent task records
        """
        tasks = self.memory.get("past_tasks", [])
        recent = tasks[-count:] if len(tasks) > count else tasks
        print(f"📋 Retrieved {len(recent)} recent tasks")
        return recent
    
    def add_note(self, note):
        """
        Add a note to memory
        
        Args:
            note (str): The note to add
        """
        note_record = {
            "timestamp": datetime.now().isoformat(),
            "note": note
        }
        self.memory["notes"].append(note_record)
        print(f"📌 Note added: {note[:50]}...")
        self._save_memory()
    
    def display_summary(self):
        """Display a summary of what's in memory"""
        print("\n" + "="*60)
        print("💾 MEMORY SUMMARY")
        print("="*60)
        
        print(f"\n🎨 Brand:")
        print(f"   Voice: {self.memory['brand']['voice']}")
        print(f"   Colors: {self.memory['brand']['colors'] or 'Not set'}")
        print(f"   Audience: {self.memory['brand']['target_audience'] or 'Not set'}")
        
        print(f"\n💰 Budget:")
        print(f"   Monthly: ${self.memory['budget']['monthly']}")
        print(f"   Spent: ${self.memory['budget']['spent']}")
        print(f"   Remaining: ${self.memory['budget']['remaining']}")
        
        print(f"\n📋 Tasks Completed: {len(self.memory['past_tasks'])}")
        
        print(f"\n📌 Notes: {len(self.memory['notes'])}")
        
        print("="*60)


# Test the memory system
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING MEMORY SYSTEM")
    print("="*60)
    
    # Create memory system
    memory = MemorySystem()
    
    # Test storing brand info
    print("\n--- Testing Brand Storage ---")
    memory.store("voice", "casual and friendly", category="brand")
    memory.store("colors", ["blue", "white"], category="brand")
    memory.store("target_audience", "small business owners", category="brand")
    
    # Test storing budget
    print("\n--- Testing Budget Storage ---")
    memory.store("monthly", 500, category="budget")
    memory.store("spent", 150, category="budget")
    memory.store("remaining", 350, category="budget")
    
    # Test logging tasks
    print("\n--- Testing Task Logging ---")
    memory.log_task(
        "Write blog post about email marketing",
        "Generated 500-word post",
        "content"
    )
    
    # Test adding notes
    print("\n--- Testing Notes ---")
    memory.add_note("Remember to focus on SEO keywords in future posts")
    
    # Test retrieving
    print("\n--- Testing Retrieval ---")
    brand_voice = memory.retrieve("voice", category="brand")
    budget_remaining = memory.retrieve("remaining", category="budget")
    
    # Display summary
    memory.display_summary()
    
    print("\n✅ Memory system test complete!")