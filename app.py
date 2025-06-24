import streamlit as st
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from auth import authenticate_user, register_user
from database import initialize_database, get_user_profile, save_user_profile, get_user_transactions, save_transaction, delete_transaction
from ai_agent import FinancialAgent
from profile_builder import ProfileBuilder

# Initialize database
initialize_database()

# Page configuration
st.set_page_config(
    page_title="FinAI - Your Financial Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application function"""
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'profile_complete' not in st.session_state:
        st.session_state.profile_complete = False
    
    # Authentication flow
    if not st.session_state.authenticated:
        show_auth_page()
    else:
        # Check if profile is complete
        if not st.session_state.profile_complete:
            check_profile_completion()
        
        if not st.session_state.profile_complete:
            show_profile_builder()
        else:
            show_dashboard()

def show_auth_page():
    """Display authentication page"""
    st.title("🤖 FinAI - Your Personal Financial Assistant")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Welcome Back!")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if username and password:
                    user_data = authenticate_user(username, password)
                    if user_data:
                        st.session_state.authenticated = True
                        st.session_state.user_id = user_data['id']
                        st.session_state.username = user_data['username']
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please fill in all fields")
    
    with tab2:
        st.subheader("Create Your Account")
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            email = st.text_input("Email Address")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_button = st.form_submit_button("Register")
            
            if register_button:
                if new_username and email and new_password and confirm_password:
                    if new_password == confirm_password:
                        if register_user(new_username, email, new_password):
                            st.success("Registration successful! Please login.")
                        else:
                            st.error("Username already exists")
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill in all fields")

def check_profile_completion():
    """Check if user profile is complete"""
    conn = sqlite3.connect('finai.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT profile_complete FROM users WHERE id = ?", (st.session_state.user_id,))
    result = cursor.fetchone()
    
    if result and result[0]:
        st.session_state.profile_complete = True
    
    conn.close()

def show_profile_builder():
    """Display profile builder"""
    st.title("📝 Let's Build Your Financial Profile")
    st.markdown("Help us understand your financial situation better to provide personalized recommendations.")
    
    profile_builder = ProfileBuilder(st.session_state.user_id)
    
    if profile_builder.build_profile():
        st.session_state.profile_complete = True
        st.success("Profile completed successfully!")
        st.balloons()
        st.rerun()

def show_dashboard():
    """Display simplified dashboard"""
    # Sidebar navigation
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}!")
        st.markdown("---")
        
        page = st.selectbox(
            "Navigate to:",
            ["Dashboard", "Add Transaction", "View Transactions", "AI Insights", "Profile Settings"]
        )
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.profile_complete = False
            st.rerun()
    
    # Main content area
    if page == "Dashboard":
        show_main_dashboard()
    elif page == "Add Transaction":
        show_add_transaction()
    elif page == "View Transactions":
        show_transactions()
    elif page == "AI Insights":
        show_ai_insights()
    elif page == "Profile Settings":
        show_profile_settings()

from database import delete_transaction  # Make sure this is at the top of your file



def show_main_dashboard():
    """Display main dashboard"""
    st.title("💰 FinAI Dashboard")
    
    # Get user profile
    user_profile = get_user_profile(st.session_state.user_id)
    if user_profile and user_profile.get('name'):
        st.markdown(f"### Welcome back, {user_profile['name']}! 👋")
    
    # Financial overview
    transactions = get_user_transactions(st.session_state.user_id, limit=10)
    
    col1, col2, col3 = st.columns(3)
    
    # Calculate basic metrics
    total_spent = sum(t['amount'] for t in transactions if t['transaction_type'] == 'debit')
    total_received = sum(t['amount'] for t in transactions if t['transaction_type'] == 'credit')
    transaction_count = len(transactions)
    
    with col1:
        st.metric("Total Spent", f"₹{total_spent:,.2f}")
    
    with col2:
        st.metric("Total Received", f"₹{total_received:,.2f}")
    
    with col3:
        st.metric("Transactions", str(transaction_count))
    
    st.markdown("---")
    
    # Recent transactions
    st.markdown("### 💳 Recent Transactions")
    
    if not transactions:
        st.info("No transactions found. Add your first transaction to get started!")
    else:
        for transaction in transactions[:5]:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                icon = "📤" if transaction['transaction_type'] == 'debit' else "📥"
                st.write(f"{icon} **{transaction.get('description', 'Transaction')}**")
                if transaction.get('merchant'):
                    st.caption(f"at {transaction['merchant']}")
            
            with col2:
                amount = transaction.get('amount', 0)
                if transaction['transaction_type'] == 'debit':
                    st.markdown(f"<span style='color: #ff6b6b'>-₹{amount:,.2f}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color: #51cf66'>+₹{amount:,.2f}</span>", unsafe_allow_html=True)
            
            with col3:
                st.write(transaction.get('date', 'Unknown'))
                st.caption(transaction.get('category', 'Others'))

            with col4:
                if st.button("🗑️", key=f"recent_delete_{transaction['id']}"):
                    delete_transaction(transaction["id"])
                    st.success("Transaction deleted.")
                    st.rerun()

            st.markdown("---")
    
    # AI Recommendations
    st.markdown("### 🤖 AI Recommendations")

    try:
        ai_agent = FinancialAgent(st.session_state.user_id)
        recommendations = ai_agent.generate_recommendations(context="Based on your recent transaction")

        if recommendations:
            for rec in recommendations[:3]:
                with st.expander(f"💡 {rec.get('title', 'Financial Tip')}", expanded=False):
                    st.write(rec.get('description', ''))
                    if rec.get('potential_savings'):  # Display potential savings
                        st.markdown(f"**Potential Savings:** {rec['potential_savings']}")
                    if rec.get('action_items'):
                        st.markdown("**Action Items:**")
                        st.write(rec['action_items'])
        else:
            st.info("Add more transactions to get personalized AI recommendations!")
    except Exception as e:
        st.error(f"Error generating recommendations: {str(e)}")



def show_add_transaction():
    """Add transaction manually"""
    st.title("💳 Add Transaction")
    
    if st.session_state.get("transaction_success"):
        st.success("✅ Transaction added successfully!")
        st.session_state.transaction_success = False 

    with st.form("add_transaction"):
        col1, col2 = st.columns(2)
        
        with col1:
            transaction_type = st.selectbox("Type", ["debit", "credit"])
            amount = st.number_input("Amount (₹)", min_value=0.01, step=0.01)
            description = st.text_input("Description")
            
        with col2:
            category = st.selectbox("Category", [
                "Food & Dining", "Shopping", "Transportation", "Utilities", 
                "Healthcare", "Entertainment", "ATM", "Transfer", "Investment", 
                "Insurance", "Groceries", "Fuel", "Others"
            ])
            merchant = st.text_input("Merchant (optional)")
            transaction_date = st.date_input("Date", value=datetime.now().date())
        
        submitted = st.form_submit_button("Add Transaction")
        
        if submitted:
            if amount > 0 and description:
                transaction_data = {
                    'transaction_type': transaction_type,
                    'amount': amount,
                    'description': description,
                    'category': category,
                    'merchant': merchant if merchant else None,
                    'date': transaction_date.strftime('%Y-%m-%d'),
                    'source': 'manual',
                    'ai_confidence': 1.0
                }
                
                if save_transaction(st.session_state.user_id, transaction_data):
                    st.session_state.transaction_success = True
                    st.rerun()

                else:
                    st.error("Failed to save transaction.")
            else:
                st.error("Please fill in all required fields.")

def show_transactions():
    """Show all transactions with delete button"""
    st.title("💳 Transaction History")
    
    transactions = get_user_transactions(st.session_state.user_id, limit=100)
    
    if not transactions:
        st.info("No transactions found.")
        return

    for transaction in transactions:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])

        with col1:
            st.write(f"**{transaction.get('description', 'Transaction')}**")
            st.caption(f"Date: {transaction.get('date', 'Unknown')}")

        with col2:
            st.write(f"Category: {transaction.get('category', 'Others')}")
            if transaction.get('merchant'):
                st.caption(f"Merchant: {transaction['merchant']}")

        with col3:
            amount = transaction.get('amount', 0)
            if transaction['transaction_type'] == 'debit':
                st.markdown(f"<span style='color: #ff6b6b'>-₹{amount:,.2f}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color: #51cf66'>+₹{amount:,.2f}</span>", unsafe_allow_html=True)

        with col4:
            st.caption(f"Source: {transaction.get('source', 'Unknown')}")

        with col5:
            # Unique key per button
            if st.button("🗑️", key=f"delete_btn_{transaction['id']}"):
                delete_transaction(transaction["id"])
                st.success("Transaction deleted.")
                st.rerun()

        st.markdown("---")

def show_ai_insights():
    """Show AI insights"""
    st.title("🤖 AI Financial Insights")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Generate Insights"):
            with st.spinner("AI is analyzing your financial data..."):
                try:
                    ai_agent = FinancialAgent(st.session_state.user_id)
                    insights = ai_agent.analyze_spending_patterns()
                    if insights:
                        st.success(f"Generated {len(insights)} new insights!")
                        st.rerun()
                    else:
                        st.warning("No new insights generated.")
                except Exception as e:
                    st.error(f"Error generating insights: {str(e)}")
    
    # Show existing insights
    from database import get_user_insights
    insights = get_user_insights(st.session_state.user_id, limit=5)
    
    if not insights:
        st.info("No insights available yet. Add more transactions and generate insights.")
        return
    
    for insight in insights:
        priority = insight.get('priority', 3)
        if priority == 1:
            st.error(f"🔴 **{insight.get('title', 'Insight')}**")
        elif priority == 2:
            st.warning(f"🟡 **{insight.get('title', 'Insight')}**")
        else:
            st.info(f"🟢 **{insight.get('title', 'Insight')}**")
        
        st.write(insight.get('description', ''))
        st.caption(f"Category: {insight.get('category', 'General')} | Confidence: {insight.get('confidence', 0):.0%}")
        st.markdown("---")

def show_profile_settings():
    """Show profile settings"""
    st.title("⚙️ Profile Settings")
    
    user_profile = get_user_profile(st.session_state.user_id)
    
    if not user_profile:
        st.error("Profile not found.")
        return
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name", value=user_profile.get('name', ''))
            age_group = st.selectbox(
                "Age Group",
                ["<25", "25–35", "35–50", ">50"],
                index=["<25", "25–35", "35–50", ">50"].index(user_profile.get('age_group', '<25')) if user_profile.get('age_group') in ["<25", "25–35", "35–50", ">50"] else 0
            )
            income_range = st.selectbox(
                "Monthly Income",
                ["<30K", "30K–50K", "50K–1L", ">1L"],
                index=["<30K", "30K–50K", "50K–1L", ">1L"].index(user_profile.get('income_range', '<30K')) if user_profile.get('income_range') in ["<30K", "30K–50K", "50K–1L", ">1L"] else 0
            )
            marital_status = st.selectbox(
                "Marital Status",
                ["Yes", "No"],
                index=["Yes", "No"].index(user_profile.get('marital_status', 'No')) if user_profile.get('marital_status') in ["Yes", "No"] else 1
            )
            
        with col2:
            financial_style = st.selectbox(
                "Financial Style",
                ["Planner", "Impulsive spender", "Flexible saver"],
                index=["Planner", "Impulsive spender", "Flexible saver"].index(user_profile.get('financial_style', 'Flexible saver')) if user_profile.get('financial_style') in ["Planner", "Impulsive spender", "Flexible saver"] else 2
            )
            monthly_expenses = st.selectbox(
                "Monthly Expenses",
                ["<20K", "20K–40K", "40K–70K", ">70K"],
                index=["<20K", "20K–40K", "40K–70K", ">70K"].index(user_profile.get('monthly_expenses', '<20K')) if user_profile.get('monthly_expenses') in ["<20K", "20K–40K", "40K–70K", ">70K"] else 0
            )
            investment_experience = st.selectbox(
                "Investment Experience",
                ["Yes", "No", "Sometimes"],
                index=["Yes", "No", "Sometimes"].index(user_profile.get('investment_experience', 'No')) if user_profile.get('investment_experience') in ["Yes", "No", "Sometimes"] else 1
            )
            debt_status = st.selectbox(
                "Debt Status",
                ["No debts", "Some debts", "Heavy debts"],
                index=["No debts", "Some debts", "Heavy debts"].index(user_profile.get('debt_status', 'No debts')) if user_profile.get('debt_status') in ["No debts", "Some debts", "Heavy debts"] else 0
            )
        
        financial_goals = st.selectbox(
            "Financial Goals",
            ["Savings", "Investment", "Debt clearance", "Retirement planning"],
            index=["Savings", "Investment", "Debt clearance", "Retirement planning"].index(user_profile.get('financial_goals', 'Savings')) if user_profile.get('financial_goals') in ["Savings", "Investment", "Debt clearance", "Retirement planning"] else 0
        )
        
        submitted = st.form_submit_button("Update Profile")
        
        if submitted:
            updated_profile = {
                'name': name,
                'age_group': age_group,
                'income_range': income_range,
                'marital_status': marital_status,
                'financial_style': financial_style,
                'monthly_expenses': monthly_expenses,
                'investment_experience': investment_experience,
                'debt_status': debt_status,
                'financial_goals': financial_goals
            }
            
            save_user_profile(st.session_state.user_id, updated_profile)
            st.success("Profile updated successfully!")
            st.rerun()

if __name__ == "__main__":
    main()