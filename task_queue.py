"""
Task Queue System - Batch Processing for Multiple Tasks
Queue and execute multiple tasks efficiently
"""

from datetime import datetime
import json

class TaskQueue:
    """
    Task queue for batching and managing multiple tasks
    """
    
    def __init__(self, memory_system=None):
        """
        Initialize task queue
        
        Args:
            memory_system: Optional memory system for logging
        """
        self.queue = []
        self.completed = []
        self.failed = []
        self.memory = memory_system
        print("📋 Task Queue initialized")
    
    def add_task(self, task_type, task_data, priority=5):
        """
        Add a task to the queue
        
        Args:
            task_type (str): Type of task (research, content, seo, etc.)
            task_data (dict): Task parameters
            priority (int): Priority (1-10, lower = higher priority)
            
        Returns:
            str: Task ID
        """
        task_id = f"task_{len(self.queue) + 1}_{datetime.now().strftime('%H%M%S')}"
        
        task = {
            'id': task_id,
            'type': task_type,
            'data': task_data,
            'priority': priority,
            'status': 'queued',
            'added_at': datetime.now().isoformat(),
            'result': None
        }
        
        self.queue.append(task)
        
        print(f"✅ Task added to queue: {task_id}")
        print(f"   Type: {task_type}")
        print(f"   Priority: {priority}")
        print(f"   Queue size: {len(self.queue)}")
        
        return task_id
    
    def add_batch(self, tasks):
        """
        Add multiple tasks at once
        
        Args:
            tasks (list): List of task dicts with 'type' and 'data'
            
        Returns:
            list: List of task IDs
        """
        task_ids = []
        
        print(f"\n📦 Adding batch of {len(tasks)} tasks...")
        
        for task in tasks:
            task_id = self.add_task(
                task_type=task['type'],
                task_data=task['data'],
                priority=task.get('priority', 5)
            )
            task_ids.append(task_id)
        
        print(f"✅ Batch added: {len(task_ids)} tasks queued")
        
        return task_ids
    
    def sort_by_priority(self):
        """Sort queue by priority (lower number = higher priority)"""
        self.queue.sort(key=lambda x: x['priority'])
        print(f"🔀 Queue sorted by priority")
    
    def execute_queue(self, nexus=None):
        """
        Execute all tasks in the queue
        
        Args:
            nexus: The Nexus orchestrator to execute tasks
            
        Returns:
            dict: Execution results
        """
        if not self.queue:
            print("⚠️ Queue is empty!")
            return {'completed': [], 'failed': []}
        
        print("\n" + "="*60)
        print(f"🚀 EXECUTING TASK QUEUE ({len(self.queue)} tasks)")
        print("="*60)
        
        # Sort by priority first
        self.sort_by_priority()
        
        total = len(self.queue)
        
        while self.queue:
            task = self.queue.pop(0)
            task_num = total - len(self.queue)
            
            print(f"\n--- Task {task_num}/{total} ---")
            print(f"ID: {task['id']}")
            print(f"Type: {task['type']}")
            print(f"Priority: {task['priority']}")
            
            try:
                task['status'] = 'running'
                task['started_at'] = datetime.now().isoformat()
                
                # Execute based on task type
                result = self._execute_task(task, nexus)
                
                task['status'] = 'completed'
                task['completed_at'] = datetime.now().isoformat()
                task['result'] = result
                
                self.completed.append(task)
                
                print(f"✅ Task {task_num} completed")
                
            except Exception as e:
                task['status'] = 'failed'
                task['error'] = str(e)
                task['failed_at'] = datetime.now().isoformat()
                
                self.failed.append(task)
                
                print(f"❌ Task {task_num} failed: {e}")
        
        print("\n" + "="*60)
        print("📊 QUEUE EXECUTION COMPLETE")
        print("="*60)
        print(f"✅ Completed: {len(self.completed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print("="*60)
        
        # Log to memory if available
        if self.memory:
            self.memory.log_task(
                task_description=f"Batch execution: {total} tasks",
                result_summary=f"{len(self.completed)} completed, {len(self.failed)} failed",
                agent_used="task_queue"
            )
        
        return {
            'completed': self.completed,
            'failed': self.failed,
            'total': total
        }
    
    def _execute_task(self, task, nexus):
        """
        Execute a single task
        
        Args:
            task (dict): Task to execute
            nexus: Nexus orchestrator
            
        Returns:
            Result from task execution
        """
        task_type = task['type']
        task_data = task['data']
        
        # If nexus is provided, use it
        if nexus:
            return nexus.execute_task(task_data.get('goal', ''))
        
        # Otherwise, execute based on type
        if task_type == 'research':
            from research_agent import research_topic
            return research_topic(task_data['topic'], task_data.get('num_results', 5))
        
        elif task_type == 'seo':
            from seo_agent import find_keywords
            return find_keywords(task_data['topic'], task_data.get('num_keywords', 10))
        
        elif task_type == 'content':
            from content_agent import generate_content
            return generate_content(task_data['prompt'])
        
        elif task_type == 'ppc':
            from ppc_agent import create_campaign_strategy
            return create_campaign_strategy(task_data['campaign'], task_data.get('budget'))
        
        elif task_type == 'crm':
            from crm_agent import create_email_sequence
            return create_email_sequence(
                task_data['purpose'],
                task_data.get('num_emails', 5),
                task_data.get('audience', 'general')
            )
        
        elif task_type == 'analytics':
            from analytics_agent import analyze_performance
            return analyze_performance(task_data['description'], task_data['data'])
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def get_status(self):
        """Get current queue status"""
        status = {
            'queued': len(self.queue),
            'completed': len(self.completed),
            'failed': len(self.failed),
            'total_processed': len(self.completed) + len(self.failed)
        }
        
        print("\n📊 QUEUE STATUS")
        print("="*60)
        print(f"Queued: {status['queued']}")
        print(f"Completed: {status['completed']}")
        print(f"Failed: {status['failed']}")
        print(f"Total Processed: {status['total_processed']}")
        print("="*60)
        
        return status
    
    def clear_completed(self):
        """Clear completed tasks"""
        count = len(self.completed)
        self.completed = []
        print(f"🗑️ Cleared {count} completed tasks")
    
    def clear_all(self):
        """Clear all tasks"""
        total = len(self.queue) + len(self.completed) + len(self.failed)
        self.queue = []
        self.completed = []
        self.failed = []
        print(f"🗑️ Cleared all {total} tasks")
    
    def export_results(self, filename="queue_results.json"):
        """
        Export results to JSON file
        
        Args:
            filename (str): Output filename
        """
        results = {
            'completed': self.completed,
            'failed': self.failed,
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results exported to {filename}")
        return filename


# Test task queue
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING TASK QUEUE SYSTEM")
    print("="*60)
    
    # Create queue
    queue = TaskQueue()
    
    # Test 1: Add single task
    print("\n--- Test 1: Add Single Task ---")
    queue.add_task(
        task_type='content',
        task_data={'prompt': 'Write 3 marketing tips'},
        priority=5
    )
    
    # Test 2: Add batch
    print("\n--- Test 2: Add Batch Tasks ---")
    batch = [
        {
            'type': 'content',
            'data': {'prompt': 'Write a tagline for coffee shop'},
            'priority': 3
        },
        {
            'type': 'content',
            'data': {'prompt': 'Write 5 Instagram captions'},
            'priority': 7
        },
        {
            'type': 'content',
            'data': {'prompt': 'Write email subject line'},
            'priority': 5
        }
    ]
    
    queue.add_batch(batch)
    
    # Test 3: Check status
    print("\n--- Test 3: Queue Status ---")
    queue.get_status()
    
    # Test 4: Sort by priority
    print("\n--- Test 4: Sort by Priority ---")
    queue.sort_by_priority()
    print("Priority order:")
    for i, task in enumerate(queue.queue, 1):
        print(f"  {i}. {task['id']} - Priority {task['priority']}")
    
    print("\n" + "="*60)
    print("✅ Task Queue System Ready!")
    print("="*60)
    
    print("\nTo execute queue:")
    print("  results = queue.execute_queue(nexus)")