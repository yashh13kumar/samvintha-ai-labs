import streamlit as st
from typing import Dict, List
from database import save_user_profile, get_user_profile
from auth import update_user_profile_status

class ProfileBuilder:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.profile_questions = [
            {"key": "name", "q": "👋 What should I call you?", "type": "text"},
            {"key": "age_group", "q": "📊 Your age group?", "options": ["<25", "25–35", "35–50", ">50"], "type": "select"},
            {"key": "income_range", "q": "💼 Monthly income range?", "options": ["<30K", "30K–50K", "50K–1L", ">1L"], "type": "select"},
            {"key": "savings_style", "q": "💰 Savings style?", "options": ["Fixed", "Varies", "Rarely save"], "type": "select"},
            {"key": "marital_status", "q": "❤️ Are you married?", "options": ["Yes", "No"], "type": "select"},
            {"key": "financial_style", "q": "🧠 Your financial style?", "options": ["Planner", "Impulsive spender", "Flexible saver"], "type": "select"},
            {"key": "monthly_expenses", "q": "💸 Approximate monthly expenses?", "options": ["<20K", "20K–40K", "40K–70K", ">70K"], "type": "select"},
            {"key": "investment_experience", "q": "📈 Do you invest regularly?", "options": ["Yes", "No", "Sometimes"], "type": "select"},
            {"key": "debt_status", "q": "💳 Do you have outstanding debts?", "options": ["No debts", "Some debts", "Heavy debts"], "type": "select"},
            {"key": "financial_goals", "q": "🎯 Your main financial goal?", "options": ["Savings", "Investment", "Debt clearance", "Retirement planning"], "type": "select"}
        ]
        
        # Initialize session state for profile data
        if 'profile_data' not in st.session_state:
            st.session_state.profile_data = {}
        
        # Initialize current question index
        if 'current_question' not in st.session_state:
            st.session_state.current_question = 0
    
    def build_profile(self) -> bool:
        """Build user profile through conversational interface"""
        
        # Check if profile already exists
        existing_profile = get_user_profile(self.user_id)
        if existing_profile:
            return self.show_existing_profile(existing_profile)
        
        # Progress bar
        progress = st.session_state.current_question / len(self.profile_questions)
        st.progress(progress)
        
        st.markdown(f"**Question {st.session_state.current_question + 1} of {len(self.profile_questions)}**")
        
        # Get current question
        current_q = self.profile_questions[st.session_state.current_question]
        
        # Display question
        st.markdown(f"### {current_q['q']}")
        
        # Handle different question types
        if current_q['type'] == 'text':
            answer = st.text_input("Your answer:", key=f"q_{current_q['key']}")
        elif current_q['type'] == 'select':
            answer = st.selectbox("Choose an option:", [""] + current_q['options'], key=f"q_{current_q['key']}")
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.session_state.current_question > 0:
                if st.button("← Previous"):
                    st.session_state.current_question -= 1
                    st.rerun()
        
        with col2:
            if answer and answer.strip():
                # Store the answer
                st.session_state.profile_data[current_q['key']] = answer
                
                if st.session_state.current_question < len(self.profile_questions) - 1:
                    if st.button("Next →"):
                        st.session_state.current_question += 1
                        st.rerun()
                else:
                    if st.button("Complete Profile ✓"):
                        return self.save_profile()
        
        with col3:
            if st.button("Skip"):
                if st.session_state.current_question < len(self.profile_questions) - 1:
                    st.session_state.current_question += 1
                    st.rerun()
                else:
                    return self.save_profile()
        
        # Show current answers
        if st.session_state.profile_data:
            st.markdown("---")
            st.markdown("**Your answers so far:**")
            for i, question in enumerate(self.profile_questions[:st.session_state.current_question + 1]):
                if question['key'] in st.session_state.profile_data:
                    st.write(f"**{question['q']}** {st.session_state.profile_data[question['key']]}")
        
        return False
    
    def save_profile(self) -> bool:
        """Save the completed profile"""
        try:
            # Save to database
            save_user_profile(self.user_id, st.session_state.profile_data)
            
            # Update user profile completion status
            update_user_profile_status(self.user_id, True)
            
            # Clear session state
            st.session_state.profile_data = {}
            st.session_state.current_question = 0
            
            return True
            
        except Exception as e:
            st.error(f"Error saving profile: {str(e)}")
            return False
    
    def show_existing_profile(self, profile: Dict) -> bool:
        """Show existing profile with option to edit"""
        st.markdown("### 📋 Your Profile")
        st.info("You already have a profile. You can view it below or update it.")
        
        # Display current profile
        profile_display = {
            "name": "👋 Name",
            "age_group": "📊 Age Group",
            "income_range": "💼 Income Range",
            "savings_style": "💰 Savings Style",
            "marital_status": "❤️ Marital Status",
            "financial_style": "🧠 Financial Style",
            "monthly_expenses": "💸 Monthly Expenses",
            "investment_experience": "📈 Investment Experience",
            "debt_status": "💳 Debt Status",
            "financial_goals": "🎯 Financial Goals"
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            for key, label in list(profile_display.items())[:5]:
                if profile.get(key):
                    st.write(f"**{label}:** {profile[key]}")
        
        with col2:
            for key, label in list(profile_display.items())[5:]:
                if profile.get(key):
                    st.write(f"**{label}:** {profile[key]}")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✏️ Update Profile"):
                st.session_state.current_question = 0
                st.session_state.profile_data = {}
                st.rerun()
        
        with col2:
            if st.button("✅ Continue to Dashboard"):
                return True
        
        return True
    
    def get_profile_summary(self) -> str:
        """Get a summary of the user's profile for AI analysis"""
        profile = get_user_profile(self.user_id)
        
        if not profile:
            return "No profile data available"
        
        summary_parts = []
        
        if profile.get('name'):
            summary_parts.append(f"Name: {profile['name']}")
        
        if profile.get('age_group'):
            summary_parts.append(f"Age: {profile['age_group']}")
        
        if profile.get('income_range'):
            summary_parts.append(f"Income: {profile['income_range']}")
        
        if profile.get('financial_style'):
            summary_parts.append(f"Style: {profile['financial_style']}")
        
        if profile.get('financial_goals'):
            summary_parts.append(f"Goals: {profile['financial_goals']}")
        
        if profile.get('debt_status'):
            summary_parts.append(f"Debt: {profile['debt_status']}")
        
        return "; ".join(summary_parts)
    
    def validate_profile_completeness(self) -> Dict[str, bool]:
        """Validate if profile is complete"""
        profile = get_user_profile(self.user_id)
        
        if not profile:
            return {"complete": False, "missing_fields": list(self.profile_questions)}
        
        missing_fields = []
        for question in self.profile_questions:
            if not profile.get(question['key']):
                missing_fields.append(question)
        
        return {
            "complete": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "completion_percentage": ((len(self.profile_questions) - len(missing_fields)) / len(self.profile_questions)) * 100
        }
    
    def get_profile_insights(self) -> List[str]:
        """Get insights based on user profile"""
        profile = get_user_profile(self.user_id)
        
        if not profile:
            return ["Complete your profile to get personalized insights!"]
        
        insights = []
        
        # Age-based insights
        if profile.get('age_group') == '<25':
            insights.append("🎯 Starting early with financial planning gives you a huge advantage!")
        elif profile.get('age_group') == '>50':
            insights.append("🏖️ Focus on retirement planning and wealth preservation.")
        
        # Income and expense insights
        if profile.get('income_range') and profile.get('monthly_expenses'):
            insights.append("📊 We'll help you optimize the gap between income and expenses.")
        
        # Investment insights
        if profile.get('investment_experience') == 'No':
            insights.append("💡 We'll suggest beginner-friendly investment options for you.")
        elif profile.get('investment_experience') == 'Yes':
            insights.append("📈 Great! We'll provide advanced investment strategies.")
        
        # Debt management
        if profile.get('debt_status') == 'Heavy debts':
            insights.append("🎯 Priority: Let's create a debt payoff strategy.")
        elif profile.get('debt_status') == 'No debts':
            insights.append("✨ Excellent! You can focus on wealth building.")
        
        # Financial style insights
        if profile.get('financial_style') == 'Planner':
            insights.append("📋 Perfect! We'll provide detailed financial planning tools.")
        elif profile.get('financial_style') == 'Impulsive spender':
            insights.append("🛡️ We'll help you with smart spending habits and budgeting.")
        
        return insights if insights else ["Your profile looks great! Ready for personalized recommendations."]