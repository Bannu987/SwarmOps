"""
Enhanced Memory System - Advanced Storage and Retrieval
Improved memory with better organization, search, and tracking
"""

import json
import os
from datetime import datetime
from collections import defaultdict

class EnhancedMemory:
    """
    Enhanced memory system with advanced features:
    - Campaign tracking
    - Agent collaboration history
    - Performance metrics
    - Advanced search
    - Data export
    """
    
    def __init__(self, memory_file="enhanced_memory.json"):
        """Initialize enhanced memory system"""
        self.memory_file = memory_file
        self.memory = self._load_memory()
        print(f"💾 Enhanced Memory System initialized")
        print(f"📁 Memory file: {self.memory_file}")
        self._print_stats()
    
    def _load_memory(self):
        """Load memory from JSON file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    memory = json.load(f)
                    return memory
            except json.JSONDecodeError:
                print("⚠️ Memory file corrupted, creating new one")
                return self._create_default_memory()
        else:
            return self._create_default_memory()
    
    def _create_default_memory(self):
        """Create default memory structure"""
        return {
            "campaigns": [],
            "agent_interactions": [],
            "tasks": [],
            "performance_metrics": {},
            "workflows": [],
            "settings": {
                "created_at": datetime.now().isoformat(),
                "version": "2.0"
            }
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
    
    def _print_stats(self):
        """Print memory statistics"""
        stats = self.get_stats()
        print(f"📊 Campaigns: {stats['campaigns']}")
        print(f"📊 Tasks: {stats['tasks']}")
        print(f"📊 Interactions: {stats['interactions']}")
        print(f"📊 Workflows: {stats['workflows']}")
    
    # Campaign Management
    def create_campaign(self, name, description, goals=None):
        """
        Create a new campaign
        
        Args:
            name (str): Campaign name
            description (str): Campaign description
            goals (list): Optional list of goals
            
        Returns:
            str: Campaign ID
        """
        campaign_id = f"campaign_{len(self.memory['campaigns']) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        campaign = {
            'id': campaign_id,
            'name': name,
            'description': description,
            'goals': goals or [],
            'tasks': [],
            'agents_used': [],
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'metrics': {}
        }
        
        self.memory['campaigns'].append(campaign)
        self._save_memory()
        
        print(f"📋 Campaign created: {name} ({campaign_id})")
        return campaign_id
    
    def add_task_to_campaign(self, campaign_id, task_data):
        """Add a task to a campaign"""
        for campaign in self.memory['campaigns']:
            if campaign['id'] == campaign_id:
                campaign['tasks'].append({
                    'task': task_data,
                    'added_at': datetime.now().isoformat()
                })
                self._save_memory()
                print(f"✅ Task added to campaign {campaign_id}")
                return True
        
        print(f"❌ Campaign {campaign_id} not found")
        return False
    
    def get_campaign(self, campaign_id):
        """Get campaign details"""
        for campaign in self.memory['campaigns']:
            if campaign['id'] == campaign_id:
                return campaign
        return None
    
    def list_campaigns(self, status=None):
        """
        List all campaigns
        
        Args:
            status (str): Filter by status (active, completed, archived)
            
        Returns:
            list: List of campaigns
        """
        campaigns = self.memory['campaigns']
        
        if status:
            campaigns = [c for c in campaigns if c.get('status') == status]
        
        print(f"\n📋 Campaigns ({len(campaigns)}):")
        print("="*60)
        
        for i, campaign in enumerate(campaigns, 1):
            print(f"\n{i}. {campaign['name']} ({campaign['id']})")
            print(f"   Status: {campaign['status']}")
            print(f"   Tasks: {len(campaign['tasks'])}")
            print(f"   Created: {campaign['created_at']}")
        
        print("="*60)
        
        return campaigns
    
    # Task Logging (Enhanced)
    def log_task(self, task_description, result_summary, agent_used, 
                 campaign_id=None, metrics=None):
        """
        Enhanced task logging
        
        Args:
            task_description (str): Description of task
            result_summary (str): Summary of result
            agent_used (str): Agent(s) that performed the task
            campaign_id (str): Optional campaign ID
            metrics (dict): Optional performance metrics
        """
        task = {
            'id': f"task_{len(self.memory['tasks']) + 1}",
            'description': task_description,
            'result': result_summary,
            'agent': agent_used,
            'campaign_id': campaign_id,
            'metrics': metrics or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.memory['tasks'].append(task)
        
        # Add to campaign if specified
        if campaign_id:
            self.add_task_to_campaign(campaign_id, task)
        
        self._save_memory()
        print(f"📝 Task logged: {task_description[:50]}...")
    
    # Agent Interaction Tracking
    def log_agent_interaction(self, source_agent, target_agent, 
                              purpose, result=None):
        """
        Log when agents communicate with each other
        
        Args:
            source_agent (str): Agent initiating
            target_agent (str): Agent being called
            purpose (str): Why they're communicating
            result (str): Optional result
        """
        interaction = {
            'id': f"interaction_{len(self.memory['agent_interactions']) + 1}",
            'from': source_agent,
            'to': target_agent,
            'purpose': purpose,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
        self.memory['agent_interactions'].append(interaction)
        self._save_memory()
        print(f"🔗 Agent interaction logged: {source_agent} → {target_agent}")
    
    def get_agent_interactions(self, agent_name=None, limit=10):
        """
        Get agent interaction history
        
        Args:
            agent_name (str): Filter by agent name
            limit (int): Number of interactions to return
            
        Returns:
            list: Interaction history
        """
        interactions = self.memory['agent_interactions']
        
        if agent_name:
            interactions = [
                i for i in interactions 
                if i['from'] == agent_name or i['to'] == agent_name
            ]
        
        return interactions[-limit:]
    
    # Performance Metrics
    def log_performance_metric(self, metric_name, value, agent=None, 
                               campaign_id=None):
        """
        Log a performance metric
        
        Args:
            metric_name (str): Name of metric
            value: Metric value
            agent (str): Optional agent name
            campaign_id (str): Optional campaign ID
        """
        if metric_name not in self.memory['performance_metrics']:
            self.memory['performance_metrics'][metric_name] = []
        
        metric = {
            'value': value,
            'agent': agent,
            'campaign_id': campaign_id,
            'timestamp': datetime.now().isoformat()
        }
        
        self.memory['performance_metrics'][metric_name].append(metric)
        self._save_memory()
        print(f"📊 Metric logged: {metric_name} = {value}")
    
    def get_metrics(self, metric_name=None):
        """Get performance metrics"""
        if metric_name:
            return self.memory['performance_metrics'].get(metric_name, [])
        return self.memory['performance_metrics']
    
    # Workflow Tracking
    def log_workflow(self, workflow_name, steps, result):
        """
        Log a completed workflow
        
        Args:
            workflow_name (str): Name of workflow
            steps (list): Steps executed
            result (str): Workflow result
        """
        workflow = {
            'id': f"workflow_{len(self.memory['workflows']) + 1}",
            'name': workflow_name,
            'steps': steps,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
        self.memory['workflows'].append(workflow)
        self._save_memory()
        print(f"🔄 Workflow logged: {workflow_name}")
    
    # Search & Retrieval
    def search_tasks(self, keyword, limit=10):
        """
        Search tasks by keyword
        
        Args:
            keyword (str): Search keyword
            limit (int): Max results
            
        Returns:
            list: Matching tasks
        """
        keyword_lower = keyword.lower()
        
        matches = [
            task for task in self.memory['tasks']
            if keyword_lower in task['description'].lower()
            or keyword_lower in task['result'].lower()
            or keyword_lower in task['agent'].lower()
        ]
        
        print(f"\n🔍 Search results for '{keyword}':")
        print(f"Found {len(matches)} matches")
        
        return matches[-limit:]
    
    def get_recent_tasks(self, agent=None, limit=10):
        """
        Get recent tasks
        
        Args:
            agent (str): Filter by agent
            limit (int): Number of tasks
            
        Returns:
            list: Recent tasks
        """
        tasks = self.memory['tasks']
        
        if agent:
            tasks = [t for t in tasks if t['agent'] == agent]
        
        return tasks[-limit:]
    
    # Statistics
    def get_stats(self):
        """Get memory statistics"""
        return {
            'campaigns': len(self.memory['campaigns']),
            'tasks': len(self.memory['tasks']),
            'interactions': len(self.memory['agent_interactions']),
            'workflows': len(self.memory['workflows']),
            'metrics': len(self.memory['performance_metrics'])
        }
    
    def get_agent_stats(self):
        """Get statistics per agent"""
        agent_stats = defaultdict(int)
        
        for task in self.memory['tasks']:
            agent_stats[task['agent']] += 1
        
        print("\n📊 Agent Statistics:")
        print("="*60)
        for agent, count in sorted(agent_stats.items(), 
                                   key=lambda x: x[1], 
                                   reverse=True):
            print(f"{agent}: {count} tasks")
        print("="*60)
        
        return dict(agent_stats)
    
    # Export
    def export_report(self, filename="memory_report.json"):
        """Export memory report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_stats(),
            'agent_stats': self.get_agent_stats(),
            'recent_tasks': self.get_recent_tasks(limit=20),
            'recent_interactions': self.get_agent_interactions(limit=20),
            'campaigns': self.memory['campaigns']
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Report exported to {filename}")
        return filename
    
    # Display
    def display_summary(self):
        """Display memory summary"""
        print("\n" + "="*60)
        print("💾 ENHANCED MEMORY SUMMARY")
        print("="*60)
        
        stats = self.get_stats()
        
        print(f"\n📋 Campaigns: {stats['campaigns']}")
        print(f"📝 Tasks: {stats['tasks']}")
        print(f"🔗 Agent Interactions: {stats['interactions']}")
        print(f"🔄 Workflows: {stats['workflows']}")
        print(f"📊 Metrics Tracked: {stats['metrics']}")
        
        print("\n🤖 Agent Activity:")
        self.get_agent_stats()
        
        print("\n📅 Recent Tasks (Last 5):")
        recent = self.get_recent_tasks(limit=5)
        for task in recent:
            print(f"  - {task['description'][:50]}... ({task['agent']})")
        
        print("="*60)


# Test enhanced memory
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING ENHANCED MEMORY SYSTEM")
    print("="*60)
    
    # Create memory
    memory = EnhancedMemory()
    
    # Test 1: Create campaign
    print("\n--- Test 1: Create Campaign ---")
    campaign_id = memory.create_campaign(
        name="Product Launch Campaign",
        description="Launch new AI product",
        goals=["Generate awareness", "Drive signups", "Create content"]
    )
    
    # Test 2: Log tasks
    print("\n--- Test 2: Log Tasks ---")
    memory.log_task(
        task_description="Research AI market trends",
        result_summary="Comprehensive research completed",
        agent_used="research",
        campaign_id=campaign_id
    )
    
    memory.log_task(
        task_description="Create SEO-optimized blog post",
        result_summary="1500-word post created",
        agent_used="seo+content",
        campaign_id=campaign_id,
        metrics={'word_count': 1500, 'keywords': 10}
    )
    
    # Test 3: Log agent interaction
    print("\n--- Test 3: Log Agent Interaction ---")
    memory.log_agent_interaction(
        source_agent="content",
        target_agent="seo",
        purpose="Get keywords for blog post",
        result="10 keywords provided"
    )
    
    # Test 4: Log metrics
    print("\n--- Test 4: Log Performance Metrics ---")
    memory.log_performance_metric("conversion_rate", 2.5, agent="ppc", campaign_id=campaign_id)
    memory.log_performance_metric("engagement_rate", 15.3, agent="content")
    
    # Test 5: Search
    print("\n--- Test 5: Search Tasks ---")
    results = memory.search_tasks("SEO")
    
    # Test 6: Display summary
    print("\n--- Test 6: Display Summary ---")
    memory.display_summary()
    
    # Test 7: Export report
    print("\n--- Test 7: Export Report ---")
    memory.export_report("test_memory_report.json")
    
    print("\n" + "="*60)
    print("✅ Enhanced Memory System Ready!")
    print("="*60)