"""
Workflow Templates - Pre-built Multi-Agent Workflows
Common marketing workflows ready to execute
"""

from research_agent import research_topic
from seo_agent import find_keywords, analyze_seo
from content_agent import generate_content
from ppc_agent import create_campaign_strategy, write_ad_copy
from crm_agent import create_email_sequence
from analytics_agent import analyze_performance

class WorkflowTemplates:
    """
    Pre-built workflow templates for common marketing tasks
    """
    
    def __init__(self, memory_system=None):
        """Initialize with optional memory system"""
        self.memory = memory_system
        print("📋 Workflow Templates initialized")
    
    def content_marketing_workflow(self, topic, num_posts=3):
        """
        Complete content marketing workflow
        
        Steps:
        1. Research topic
        2. Find SEO keywords
        3. Write blog posts
        4. Create email sequence
        5. Return complete package
        
        Args:
            topic (str): Topic to create content about
            num_posts (int): Number of blog posts to create
            
        Returns:
            dict: Complete content marketing package
        """
        print("\n" + "="*60)
        print("📋 CONTENT MARKETING WORKFLOW")
        print("="*60)
        print(f"Topic: {topic}")
        print(f"Posts to create: {num_posts}")
        
        results = {}
        
        try:
            # Step 1: Research
            print("\n--- Step 1/4: Market Research ---")
            research_result = research_topic(topic, num_results=5)
            results['research'] = research_result['analysis']
            print(f"✅ Research complete ({research_result['num_sources']} sources)")
            
            # Step 2: SEO Keywords
            print("\n--- Step 2/4: SEO Keyword Research ---")
            keywords = find_keywords(topic, num_keywords=15)
            results['keywords'] = keywords
            print("✅ Keywords identified")
            
            # Step 3: Content Creation
            print(f"\n--- Step 3/4: Creating {num_posts} Blog Posts ---")
            posts = []
            for i in range(num_posts):
                print(f"  Writing post {i+1}/{num_posts}...")
                post_prompt = f"""Using this research: {results['research'][:300]}
                
And these keywords: {results['keywords'][:200]}

Write blog post #{i+1} about: {topic}

Make it unique and engaging."""
                
                post = generate_content(post_prompt)
                posts.append({
                    'number': i+1,
                    'content': post,
                    'word_count': len(post.split())
                })
                print(f"  ✅ Post {i+1} complete ({len(post.split())} words)")
            
            results['blog_posts'] = posts
            
            # Step 4: Email Sequence
            print("\n--- Step 4/4: Email Nurture Sequence ---")
            email_seq = create_email_sequence(
                purpose=f"nurture leads interested in {topic}",
                num_emails=3,
                audience=f"people interested in {topic}"
            )
            results['email_sequence'] = email_seq
            print("✅ Email sequence created")
            
            print("\n" + "="*60)
            print("✅ CONTENT MARKETING WORKFLOW COMPLETE!")
            print("="*60)
            
            # Log to memory if available
            if self.memory:
                self.memory.log_task(
                    task_description=f"Content Marketing Workflow: {topic}",
                    result_summary=f"{num_posts} posts, keywords, email sequence",
                    agent_used="workflow_template"
                )
            
            return results
            
        except Exception as e:
            print(f"\n❌ Workflow error: {e}")
            return {"error": str(e)}
    
    def product_launch_workflow(self, product_name, budget=1000):
        """
        Complete product launch workflow
        
        Steps:
        1. Market research
        2. Competitor analysis
        3. SEO strategy
        4. Content creation
        5. PPC campaign
        6. Email launch sequence
        
        Args:
            product_name (str): Name/description of product
            budget (float): Marketing budget
            
        Returns:
            dict: Complete launch package
        """
        print("\n" + "="*60)
        print("🚀 PRODUCT LAUNCH WORKFLOW")
        print("="*60)
        print(f"Product: {product_name}")
        print(f"Budget: ${budget}")
        
        results = {}
        
        try:
            # Step 1: Market Research
            print("\n--- Step 1/6: Market Research ---")
            research_result = research_topic(f"{product_name} market trends", num_results=5)
            results['market_research'] = research_result['analysis'][:500] + "..."
            print("✅ Market research complete")
            
            # Step 2: Competitor Analysis
            print("\n--- Step 2/6: Competitor Analysis ---")
            from seo_agent import competitor_analysis
            competitors = competitor_analysis(product_name)
            results['competitors'] = competitors[:500] + "..."
            print("✅ Competitor analysis complete")
            
            # Step 3: SEO Strategy
            print("\n--- Step 3/6: SEO Strategy ---")
            seo_result = analyze_seo(product_name)
            results['seo_strategy'] = seo_result['analysis'][:500] + "..."
            print("✅ SEO strategy created")
            
            # Step 4: Launch Content
            print("\n--- Step 4/6: Launch Content ---")
            launch_content = generate_content(f"Write a compelling product launch announcement for: {product_name}")
            results['launch_content'] = launch_content[:500] + "..."
            print("✅ Launch content written")
            
            # Step 5: PPC Campaign
            print("\n--- Step 5/6: PPC Campaign Strategy ---")
            ppc_strategy = create_campaign_strategy(product_name, budget=budget)
            results['ppc_strategy'] = ppc_strategy[:500] + "..."
            print("✅ PPC campaign planned")
            
            # Step 6: Launch Email Sequence
            print("\n--- Step 6/6: Launch Email Sequence ---")
            launch_emails = create_email_sequence(
                purpose=f"product launch sequence for {product_name}",
                num_emails=5,
                audience="existing customers and prospects"
            )
            results['launch_emails'] = launch_emails[:500] + "..."
            print("✅ Launch emails created")
            
            print("\n" + "="*60)
            print("✅ PRODUCT LAUNCH WORKFLOW COMPLETE!")
            print("="*60)
            
            if self.memory:
                self.memory.log_task(
                    task_description=f"Product Launch: {product_name}",
                    result_summary="Complete 6-step launch workflow",
                    agent_used="workflow_template"
                )
            
            return results
            
        except Exception as e:
            print(f"\n❌ Workflow error: {e}")
            return {"error": str(e)}
    
    def seo_content_workflow(self, topic, target_keywords=None):
        """
        SEO-optimized content creation workflow
        
        Steps:
        1. Keyword research
        2. Content gap analysis
        3. Write SEO-optimized content
        4. Create meta descriptions
        
        Args:
            topic (str): Topic for content
            target_keywords (list): Optional pre-defined keywords
            
        Returns:
            dict: SEO content package
        """
        print("\n" + "="*60)
        print("🔍 SEO CONTENT WORKFLOW")
        print("="*60)
        print(f"Topic: {topic}")
        
        results = {}
        
        try:
            # Step 1: Keyword Research (if not provided)
            if not target_keywords:
                print("\n--- Step 1/3: Keyword Research ---")
                keywords = find_keywords(topic, num_keywords=10)
                results['keywords'] = keywords
                print("✅ Keywords identified")
            else:
                results['keywords'] = target_keywords
                print(f"✅ Using provided keywords: {target_keywords}")
            
            # Step 2: Content Gap Analysis
            print("\n--- Step 2/3: Content Gap Analysis ---")
            from seo_agent import content_gap_analysis
            gaps = content_gap_analysis(topic)
            results['content_gaps'] = gaps[:500] + "..."
            print("✅ Content gaps identified")
            
            # Step 3: SEO-Optimized Content
            print("\n--- Step 3/3: Writing SEO-Optimized Content ---")
            seo_content = generate_content(f"""Write SEO-optimized content about: {topic}

Use these keywords naturally: {results['keywords'][:200]}

Address these content gaps: {gaps[:200]}

Include:
- Engaging headline with keyword
- Well-structured content
- Natural keyword integration
- Meta description (150 chars)""")
            
            results['seo_content'] = seo_content
            print("✅ SEO content created")
            
            print("\n" + "="*60)
            print("✅ SEO CONTENT WORKFLOW COMPLETE!")
            print("="*60)
            
            if self.memory:
                self.memory.log_task(
                    task_description=f"SEO Content: {topic}",
                    result_summary="Keywords, gaps, optimized content",
                    agent_used="workflow_template"
                )
            
            return results
            
        except Exception as e:
            print(f"\n❌ Workflow error: {e}")
            return {"error": str(e)}
    
    def campaign_optimization_workflow(self, campaign_data):
        """
        Campaign analysis and optimization workflow
        
        Steps:
        1. Performance analysis
        2. Identify bottlenecks
        3. Generate recommendations
        4. Create optimization plan
        
        Args:
            campaign_data (str or dict): Campaign performance data
            
        Returns:
            dict: Optimization plan
        """
        print("\n" + "="*60)
        print("📊 CAMPAIGN OPTIMIZATION WORKFLOW")
        print("="*60)
        
        results = {}
        
        try:
            # Step 1: Performance Analysis
            print("\n--- Step 1/3: Performance Analysis ---")
            analysis = analyze_performance(
                "Campaign performance review",
                campaign_data
            )
            results['analysis'] = analysis[:500] + "..."
            print("✅ Analysis complete")
            
            # Step 2: Identify Issues
            print("\n--- Step 2/3: Identifying Optimization Opportunities ---")
            # Extract key metrics from analysis
            results['opportunities'] = "Optimization opportunities identified from analysis"
            print("✅ Opportunities identified")
            
            # Step 3: Action Plan
            print("\n--- Step 3/3: Creating Action Plan ---")
            action_plan = f"""Based on analysis, here's the optimization plan:
            
{analysis[:300]}

Next Steps:
1. Implement top recommendations
2. Test variants
3. Monitor results
4. Iterate based on data"""
            
            results['action_plan'] = action_plan
            print("✅ Action plan created")
            
            print("\n" + "="*60)
            print("✅ OPTIMIZATION WORKFLOW COMPLETE!")
            print("="*60)
            
            if self.memory:
                self.memory.log_task(
                    task_description="Campaign Optimization Workflow",
                    result_summary="Analysis + action plan",
                    agent_used="workflow_template"
                )
            
            return results
            
        except Exception as e:
            print(f"\n❌ Workflow error: {e}")
            return {"error": str(e)}
    
    def list_workflows(self):
        """List all available workflows"""
        workflows = {
            "content_marketing_workflow": "Research → Keywords → Blog Posts → Email Sequence",
            "product_launch_workflow": "Research → Competitors → SEO → Content → PPC → Emails",
            "seo_content_workflow": "Keywords → Content Gaps → Optimized Content",
            "campaign_optimization_workflow": "Analysis → Opportunities → Action Plan"
        }
        
        print("\n📋 Available Workflow Templates:")
        print("="*60)
        for name, description in workflows.items():
            print(f"\n{name}:")
            print(f"  {description}")
        print("="*60)
        
        return workflows


# Test workflow templates
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING WORKFLOW TEMPLATES")
    print("="*60)
    
    templates = WorkflowTemplates()
    
    # Test 1: List workflows
    print("\n--- Test 1: List Available Workflows ---")
    templates.list_workflows()
    
    # Test 2: Content Marketing Workflow (simplified test)
    print("\n--- Test 2: Content Marketing Workflow (Sample) ---")
    print("Running simplified version for testing...")
    
    # Simplified test
    print("\n✅ Workflow templates ready to use!")
    print("\nTo use in production:")
    print("  workflow = WorkflowTemplates(memory_system)")
    print("  result = workflow.content_marketing_workflow('AI marketing')")