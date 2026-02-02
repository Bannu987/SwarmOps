"""
Analytics Agent - Marketing Data Analyst
Uses Gemini AI for data analysis and insights
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Load environment variables
load_dotenv()

# Initialize Gemini
print("🔧 Initializing Analytics Agent...")
gemini_api_key = os.getenv('GEMINI_API_KEY')

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file!")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=gemini_api_key,
    temperature=0.3  # Lower temperature for more analytical responses
)

print("✅ Analytics Agent ready! (Powered by Gemini)")

# Analytics Report Template
analytics_template = """You are an expert marketing analytics consultant with deep expertise in data analysis, metrics interpretation, and performance optimization.

Analysis Request: {request}

Data Provided:
{data}

Provide a comprehensive analysis including:

1. **Key Metrics Summary:**
   - Calculate and present all relevant KPIs
   - Industry benchmarks comparison
   - Performance ratings (excellent, good, average, poor)

2. **Performance Analysis:**
   - What's performing well (and why)
   - What's underperforming (and why)
   - Surprising findings or anomalies

3. **Channel Comparison:**
   - Rank channels by efficiency
   - Best ROI channels
   - Cost per acquisition by channel
   - Recommended budget allocation

4. **Trends & Patterns:**
   - Emerging trends
   - Declining metrics
   - Seasonal or timing patterns

5. **Actionable Recommendations:**
   - Top 3 immediate actions (prioritized by impact)
   - Quick wins (low effort, high impact)
   - Long-term optimizations

6. **Risk Analysis:**
   - What could go wrong
   - Areas of concern
   - Mitigation strategies

Be specific with numbers, percentages, and concrete recommendations. Use clear formatting.

Your Analysis:"""

prompt = PromptTemplate(
    input_variables=["request", "data"],
    template=analytics_template
)

analytics_chain = prompt | llm


def analyze_performance(data_description, metrics_data):
    """
    Analyze marketing performance data
    
    Args:
        data_description (str): Description of what's being analyzed
        metrics_data (str or dict): The actual metrics/data
        
    Returns:
        str: Comprehensive analysis
    """
    print(f"\n📊 Analytics Agent analyzing: '{data_description}'")
    print(f"📈 Processing metrics...")
    
    # Format data if it's a dict
    if isinstance(metrics_data, dict):
        formatted_data = "\n".join([f"{k}: {v}" for k, v in metrics_data.items()])
    else:
        formatted_data = str(metrics_data)
    
    print(f"🤖 Generating insights with Gemini...")
    
    response = analytics_chain.invoke({
        "request": data_description,
        "data": formatted_data
    })
    
    result = response.content if hasattr(response, 'content') else str(response)
    
    print(f"✅ Analysis complete!")
    return result


def compare_campaigns(campaign_data):
    """
    Compare multiple campaigns
    
    Args:
        campaign_data (list or str): Data for multiple campaigns
        
    Returns:
        str: Comparative analysis
    """
    print(f"\n🔍 Comparing campaigns...")
    
    prompt_text = f"""Compare these marketing campaigns and provide:

Campaign Data:
{campaign_data}

Analysis:

1. **Performance Ranking:**
   - Rank campaigns by ROI
   - Rank by conversion rate
   - Rank by cost efficiency

2. **Winner Analysis:**
   - Why did the top performer win?
   - Key success factors
   - Replicable elements

3. **Learnings from Losers:**
   - Why did poor performers fail?
   - Common mistakes
   - What to avoid

4. **Cross-Campaign Insights:**
   - Patterns across winners
   - Common denominators
   - Universal best practices

5. **Scaling Recommendations:**
   - Which campaign to scale
   - How to scale (budget, audience, etc.)
   - Expected results from scaling

6. **Testing Recommendations:**
   - What to test next
   - Hypothesis for each test
   - Success criteria

Be data-driven and specific."""

    response = llm.invoke(prompt_text)
    result = response.content if hasattr(response, 'content') else str(response)
    
    print(f"✅ Comparison complete!")
    return result


def calculate_roi(investment, revenue, additional_metrics=None):
    """
    Calculate and analyze ROI
    
    Args:
        investment (float): Total investment/cost
        revenue (float): Total revenue generated
        additional_metrics (dict): Optional additional metrics
        
    Returns:
        str: ROI analysis
    """
    print(f"\n💰 Calculating ROI...")
    print(f"💵 Investment: ${investment}")
    print(f"💵 Revenue: ${revenue}")
    
    roi = ((revenue - investment) / investment) * 100
    profit = revenue - investment
    
    metrics_text = f"""
Investment: ${investment}
Revenue: ${revenue}
ROI: {roi:.2f}%
Profit: ${profit}
"""
    
    if additional_metrics:
        metrics_text += "\nAdditional Metrics:\n"
        metrics_text += "\n".join([f"{k}: {v}" for k, v in additional_metrics.items()])
    
    prompt_text = f"""Analyze this ROI data:

{metrics_text}

Provide:

1. **ROI Assessment:**
   - Is this ROI good, average, or poor? (with industry context)
   - How does it compare to benchmarks?
   - Rating and explanation

2. **Profitability Analysis:**
   - Break-even analysis
   - Profit margin assessment
   - Sustainability evaluation

3. **Efficiency Metrics:**
   - Return on ad spend (ROAS)
   - Customer acquisition cost (if applicable)
   - Lifetime value implications

4. **Improvement Opportunities:**
   - How to increase ROI by 10%, 25%, 50%
   - Quick wins vs. long-term improvements
   - Specific tactics for each

5. **Risk & Opportunity:**
   - What could threaten this ROI?
   - Where's the biggest opportunity?
   - Recommended next steps

Be specific with numbers and percentages."""

    response = llm.invoke(prompt_text)
    result = response.content if hasattr(response, 'content') else str(response)
    
    print(f"✅ ROI analysis complete!")
    print(f"📊 ROI: {roi:.2f}%")
    return result


def identify_bottlenecks(funnel_data):
    """
    Identify conversion funnel bottlenecks
    
    Args:
        funnel_data (str or dict): Funnel stage data
        
    Returns:
        str: Bottleneck analysis
    """
    print(f"\n🔍 Analyzing conversion funnel for bottlenecks...")
    
    if isinstance(funnel_data, dict):
        formatted_data = "\n".join([f"{k}: {v}" for k, v in funnel_data.items()])
    else:
        formatted_data = str(funnel_data)
    
    prompt_text = f"""Analyze this conversion funnel for bottlenecks:

{formatted_data}

Provide:

1. **Drop-off Analysis:**
   - Where are the biggest drop-offs?
   - Calculate drop-off rates between stages
   - Rank stages by severity of issue

2. **Bottleneck Identification:**
   - Primary bottleneck (biggest issue)
   - Secondary bottlenecks
   - Why these are happening (likely causes)

3. **Impact Calculation:**
   - If we fix the primary bottleneck, what's the potential gain?
   - Expected conversion rate improvement
   - Revenue impact estimate

4. **Prioritized Fixes:**
   - Fix #1 (highest impact, easiest)
   - Fix #2 (high impact, moderate effort)
   - Fix #3 (long-term improvement)

5. **Testing Strategy:**
   - What to A/B test
   - Hypotheses for each test
   - Success metrics

6. **Industry Benchmarks:**
   - How does this funnel compare to industry standards?
   - Which stages are above/below benchmark?

Calculate specific percentages and provide concrete recommendations."""

    response = llm.invoke(prompt_text)
    result = response.content if hasattr(response, 'content') else str(response)
    
    print(f"✅ Bottleneck analysis complete!")
    return result


def forecast_performance(historical_data, forecast_period="next month"):
    """
    Forecast future performance
    
    Args:
        historical_data (str): Historical performance data
        forecast_period (str): Period to forecast
        
    Returns:
        str: Performance forecast
    """
    print(f"\n🔮 Forecasting performance for: {forecast_period}")
    
    prompt_text = f"""Based on this historical data:

{historical_data}

Forecast performance for: {forecast_period}

Provide:

1. **Baseline Forecast:**
   - Expected metrics if trends continue
   - Confidence level (high, medium, low)
   - Key assumptions

2. **Best Case Scenario:**
   - What could happen if everything goes well
   - Probability assessment
   - Required conditions

3. **Worst Case Scenario:**
   - What could go wrong
   - Probability assessment
   - Warning signs to watch

4. **Trend Analysis:**
   - Upward trends to leverage
   - Downward trends to address
   - Seasonal factors

5. **Recommendations:**
   - Actions to maximize the forecast
   - Risks to mitigate
   - Opportunities to capitalize on

6. **Key Metrics to Monitor:**
   - Leading indicators
   - Lagging indicators
   - Alert thresholds

Be specific with numbers and timelines."""

    response = llm.invoke(prompt_text)
    result = response.content if hasattr(response, 'content') else str(response)
    
    print(f"✅ Forecast complete!")
    return result


# ==============================================================
# REAL DATA LAYER — MarketingOS 2.0 Upgrade
# Pulls LIVE data from Google Analytics 4.
# Falls back gracefully if GA4 is not configured.
# ==============================================================


def get_live_dashboard(days=30):
    """
    Pull REAL traffic + conversion data from GA4 and run AI analysis on it.
    Falls back to manual mode if GA4 is not connected.
    """
    try:
        from integrations.google_analytics import GoogleAnalytics

        ga = GoogleAnalytics()

        if not ga.available:
            print("⚠️  GA4 not configured — falling back to manual mode.")
            return analyze_performance(
                "Live dashboard requested",
                "GA4 not connected. Provide your data manually or complete the setup guide.",
            )

        print("\n📡 Pulling live data from Google Analytics 4...")

        traffic = ga.get_traffic_summary(days=days)
        sources = ga.get_traffic_sources(days=days)
        pages = ga.get_page_performance(days=days)
        events = ga.get_conversion_events(days=days)

        if not traffic:
            return "❌ Unable to pull GA4 data. Check your GA4 configuration."

        data = f"""=== LIVE GA4 DATA (Last {days} days) ===

TRAFFIC OVERVIEW:
- Sessions: {traffic['sessions']:,}
- Unique Users: {traffic['users']:,}
- Page Views: {traffic['pageviews']:,}
- Bounce Rate: {traffic['bounce_rate']}%
- Avg Session Duration: {traffic['avg_session_duration']}s
- New Users: {traffic['new_users']:,}
- Conversions: {traffic['conversions']:,}
- Conversion Rate: {traffic['conversion_rate']}%
"""

        if sources:
            data += "\nTRAFFIC SOURCES (top 10):\n"
            for s in sources[:10]:
                data += (
                    f"  {s['source']} / {s['medium']}: "
                    f"{s['sessions']:,} sessions | {s['conversions']} conversions | "
                    f"{s['conversion_rate']}% CVR\n"
                )

        if pages:
            data += "\nTOP PAGES (by sessions):\n"
            for p in pages[:10]:
                data += (
                    f"  {p['page_path']}: {p['sessions']:,} sessions | "
                    f"{p['conversions']} conversions | {p['bounce_rate']}% bounce\n"
                )

        if events:
            data += "\nKEY EVENTS:\n"
            for name, ev in list(events.items())[:15]:
                data += f"  {name}: {ev['count']:,} occurrences | {ev['conversions']} conversions\n"

        print("✅ Live data pulled! Running AI analysis...")
        return analyze_performance(f"Live GA4 dashboard — {days}-day window", data)

    except Exception as e:
        return f"❌ Live dashboard error: {e}"


def detect_live_anomalies(days=7):
    """
    Compare the last N days to the previous N-day window using real GA4 data.
    Returns a dict with any metrics that changed >20%, or None if GA4 is not set up.
    """
    try:
        from integrations.google_analytics import GoogleAnalytics

        ga = GoogleAnalytics()

        if not ga.available:
            print("⚠️  GA4 not configured — cannot detect anomalies.")
            return None

        print("\n🔍 Scanning for performance anomalies...")

        result = ga.detect_anomalies(days=days)
        if not result:
            return None

        if not result["anomalies"]:
            print("✅ No anomalies — performance is stable.")
            return {
                "status": "healthy",
                "message": f"No significant changes in the last {days} days.",
                "checked_at": result["checked_at"],
            }

        report_lines = [f"\n⚠️  ANOMALIES DETECTED (last {days} days):", "=" * 50]
        critical = 0
        for a in result["anomalies"]:
            icon = "🔴" if a["severity"] == "critical" else "🟡"
            arrow = "↑" if a["direction"] == "up" else "↓"
            report_lines.append(
                f"{icon} {a['metric']}: {arrow} {a['change_pct']}%  "
                f"(was {a['previous']}, now {a['current']})"
            )
            if a["severity"] == "critical":
                critical += 1

        report = "\n".join(report_lines)
        print(report)

        return {
            "status": "anomalies_detected",
            "critical_count": critical,
            "anomalies": result["anomalies"],
            "report": report,
            "checked_at": result["checked_at"],
        }

    except Exception as e:
        print(f"❌ Anomaly detection error: {e}")
        return None


# Test the Analytics Agent
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING ANALYTICS AGENT")
    print("="*60)
    
    try:
        # Test 1: Performance Analysis
        print("\n--- Test 1: Multi-Channel Performance Analysis ---")
        
        performance_data = {
            "PPC": "1,000 clicks, $500 spent, 20 conversions, $2,000 revenue",
            "Email": "10,000 sent, 2,500 opens (25%), 250 clicks (10% CTR), 15 conversions",
            "SEO": "5,000 organic visits, 100 conversions, $0 direct cost",
            "Social": "50,000 impressions, 1,000 clicks, 10 conversions, $200 spent"
        }
        
        analysis = analyze_performance(
            "Multi-channel marketing campaign performance",
            performance_data
        )
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE ANALYSIS")
        print("="*60)
        print(analysis)
        print("="*60)
        
        # Test 2: ROI Calculation
        print("\n--- Test 2: ROI Analysis ---")
        
        roi_analysis = calculate_roi(
            investment=1500,
            revenue=4500,
            additional_metrics={
                "Conversions": 145,
                "Cost per Conversion": "$10.34",
                "Customer Lifetime Value": "$200"
            }
        )
        
        print("\n" + "="*60)
        print("💰 ROI ANALYSIS")
        print("="*60)
        print(roi_analysis)
        print("="*60)
        
        # Test 3: Funnel Bottleneck Analysis
        print("\n--- Test 3: Conversion Funnel Analysis ---")
        
        funnel = {
            "Landing Page Views": "10,000",
            "Product Page Views": "3,000 (30% conversion)",
            "Add to Cart": "900 (30% conversion)",
            "Checkout Started": "450 (50% conversion)",
            "Purchase Completed": "180 (40% conversion)"
        }
        
        bottlenecks = identify_bottlenecks(funnel)
        
        print("\n" + "="*60)
        print("🔍 BOTTLENECK ANALYSIS")
        print("="*60)
        print(bottlenecks)
        print("="*60)
        
        print("\n✅ All Analytics Agent tests complete!")
        
    except ValueError as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure GEMINI_API_KEY is in your .env file")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()