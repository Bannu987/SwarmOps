"""
Utility functions for MarketingOS Dashboard
"""

import streamlit as st
from functools import wraps
import traceback
from datetime import datetime

def safe_execute(func):
    """Decorator for safe execution with error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            with st.expander("🔍 View Error Details"):
                st.code(traceback.format_exc())
            return None
    return wrapper

def show_loading(message="Processing..."):
    """Show a loading spinner with custom message"""
    return st.spinner(message)

def log_action(action, details=None):
    """Log user actions"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'details': details
    }
    
    if 'action_log' not in st.session_state:
        st.session_state.action_log = []
    
    st.session_state.action_log.append(log_entry)

def check_system_health():
    """Check if all system components are working"""
    health_status = {
        'os_system': False,
        'memory': False,
        'agents': False
    }
    
    try:
        if 'os_system' in st.session_state:
            health_status['os_system'] = True
            
            if hasattr(st.session_state.os_system, 'memory'):
                health_status['memory'] = True
            
            # Check if agents are accessible
            try:
                stats = st.session_state.os_system.memory.get_agent_stats()
                health_status['agents'] = len(stats) > 0
            except:
                pass
    except:
        pass
    
    return health_status

def display_system_health():
    """Display system health status"""
    health = check_system_health()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if health['os_system']:
            st.success("✅ System")
        else:
            st.error("❌ System")
    
    with col2:
        if health['memory']:
            st.success("✅ Memory")
        else:
            st.error("❌ Memory")
    
    with col3:
        if health['agents']:
            st.success("✅ Agents")
        else:
            st.error("❌ Agents")
    
    return all(health.values())