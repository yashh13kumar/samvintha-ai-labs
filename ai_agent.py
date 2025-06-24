import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from database import get_user_profile, save_ai_insight, get_user_transactions

class TransactionType(Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class InsightType(Enum):
    SPENDING_PATTERN = "spending_pattern"
    BUDGET_ALERT = "budget_alert"
    SAVINGS_OPPORTUNITY = "savings_opportunity"
    INVESTMENT_SUGGESTION = "investment_suggestion"
    DEBT_MANAGEMENT = "debt_management"

@dataclass
class Transaction:
    transaction_type: str
    amount: float
    description: str
    category: str
    date: str
    source: str
    merchant: Optional[str] = None
    location: Optional[str] = None
    ai_confidence: float = 0.0

@dataclass
class AIInsight:
    insight_type: str
    title: str
    description: str
    category: str
    priority: int
    confidence: float

class FinancialAgent:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.llm = ChatOllama(model="llama3:8b-instruct-q4_0")

    def _ask_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ], temperature=temperature)
            return response.content.strip()
        except Exception as e:
            print(f"Ollama model error: {e}")
            return ""

    def extract_transaction_from_text(self, text: str, source: str, metadata: Dict = None) -> Optional[Dict]:
        system_prompt = """You are a financial AI. Extract transaction details from raw text. Return ONLY valid JSON:
{
  "transaction_type": "debit" or "credit",
  "amount": float,
  "description": "brief description",
  "category": "Shopping, Dining, Travel etc.",
  "merchant": "name or null",
  "date": "YYYY-MM-DD",
  "ai_confidence": float
}
If not found, return: {"error": "No transaction found"}"""

        user_prompt = f"""Text: "{text}"
Source: {source}
Metadata: {json.dumps(metadata or {})}
Current date: {datetime.now().strftime('%Y-%m-%d')}"""

        response = self._ask_llm(system_prompt, user_prompt, temperature=0.1)
        try:
            data = json.loads(response)
            if "error" in data:
                return None
            data["source"] = source
            data["raw_text"] = text
            return data
        except:
            return None

    def analyze_spending_patterns(self) -> List[Dict]:
        transactions = get_user_transactions(self.user_id, limit=200)
        user_profile = get_user_profile(self.user_id)
        if not transactions:
            return []

        summary = self._prepare_transaction_summary(transactions)
        system_prompt = """You are a financial advisor AI. Analyze spending patterns and give insights in JSON:
[
  {
    "insight_type": "spending_pattern|budget_alert|savings_opportunity|investment_suggestion|debt_management",
    "title": "Short title",
    "description": "Actionable advice",
    "category": "relevant category",
    "priority": 1-5,
    "confidence": 0.0-1.0
  }
]"""
        user_prompt = f"""User Profile: {json.dumps(user_profile, indent=2)}
Transaction Summary: {json.dumps(summary, indent=2)}"""

        response = self._ask_llm(system_prompt, user_prompt, temperature=0.3)

        try:
            # Clean markdown wrappers and whitespace
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:-3].strip()
            elif response.startswith('```'):
                response = response[3:-3].strip()

            # Parse as JSON array if possible
            insights = []
            try:
                parsed_array = json.loads(response)
                if isinstance(parsed_array, list):
                    for item in parsed_array:
                        if isinstance(item, dict) and all(k in item for k in ['title', 'description', 'category', 'confidence']):
                            save_ai_insight(self.user_id, item)
                            insights.append(item)
                elif isinstance(parsed_array, dict):
                    if all(k in parsed_array for k in ['title', 'description', 'category', 'confidence']):
                        save_ai_insight(self.user_id, parsed_array)
                        insights.append(parsed_array)
            except json.JSONDecodeError:
                # Fallback: Try to extract multiple JSON blocks using regex
                json_matches = re.findall(r"\{[\s\S]*?\}", response)
                for match in json_matches:
                    try:
                        parsed = json.loads(match)
                        if all(k in parsed for k in ['title', 'description', 'category', 'confidence']):
                            save_ai_insight(self.user_id, parsed)
                            insights.append(parsed)
                    except json.JSONDecodeError:
                        continue

            # Sort and return top 5 by priority (1 = highest)
            top_insights = sorted(insights, key=lambda x: x.get("priority", 5))[:5]
            return top_insights

        except Exception as e:
            print(f"Insight parsing failed: {e}")
            return []

    def generate_recommendations(self, context: str = None) -> List[Dict]:
        user_profile = get_user_profile(self.user_id)
        transactions = get_user_transactions(self.user_id, limit=10)

        # Prepare a more detailed transaction summary
        transaction_summary = self._prepare_detailed_transaction_summary(transactions)

        # Prepare a profile summary
        profile_summary = self._prepare_profile_summary(user_profile)

        system_prompt = """You are a highly skilled personal financial advisor. Analyze the user's transaction history and financial profile to generate 1–2 personalized, actionable financial recommendations.

Your recommendations must:

Be tailored to the user's age group, income range, financial goals, debt status, and spending style.

Consider the top spending categories and patterns from the user's transactions (e.g., frequent dining, shopping spikes, low savings).

Suggest practical next steps like budgeting tips, switching to cheaper alternatives, or exploring specific investment/saving options.

Include a realistic potential savings estimate where appropriate.


{
  "recommendation_type": "savings|budgeting|food|transportation|entertainment|investment",
  "title": "Concise title",
  "description": "Detailed explanation of the recommendation and its benefits",
  "potential_savings": "Optional: Estimated savings amount (e.g., ₹500/month)",
  "action_items": "Specific steps the user can take to implement the recommendation",
  "priority": 1-3 (1 = highest priority)
}

Consider the user's age, income, financial goals, and spending habits when generating recommendations. For example:

A user under 25 with a savings goal and an impulsive spending style should be encouraged to start small automated savings or low-risk investments to build early discipline and capital.

A user aged 35–50 with a goal of debt clearance and high dining or shopping expenses should be advised on budget restructuring and possible EMI restructuring or snowballing techniques.

A user with low income and high spending on food or shopping should receive practical cost-cutting tips (e.g., shift to home-cooked meals, remove impulse subscriptions), with estimated savings figures.

A user with investment experience and a stable income should be nudged toward mutual funds, SIPs, or retirement index funds depending on goals like wealth creation or retirement.



Return ONLY the JSON array."""

        user_prompt = f"""User Profile Summary: {profile_summary}
Transaction Summary: {json.dumps(transaction_summary, indent=2)}
Context: {context or "General financial wellness"}"""

        try:
            response = self._ask_llm(system_prompt, user_prompt, temperature=0.2)  # Lowered temperature
            print(f"LLM Response: {response}")

            # Attempt to extract JSON using regex
            match = re.search(r"\[.*\]", response, re.DOTALL)  # Find JSON array
            if match:
                json_string = match.group(0)
            else:
                match = re.search(r"\{.*\}", response, re.DOTALL) # Find JSON object
                if match:
                    json_string = match.group(0)
                else:
                    print("No JSON found in LLM response")
                    return []

            recommendations = json.loads(json_string)
            print(f"Parsed Recommendations: {recommendations}")
            return recommendations
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []

    def _prepare_detailed_transaction_summary(self, transactions: List[Dict]) -> Dict:
        """Prepares a more detailed summary of transaction data."""
        if not transactions:
            return {"message": "No transactions available."}

        summary = {
            "total_transactions": len(transactions),
            "debit_transactions": 0,
            "credit_transactions": 0,
            "total_spent": 0,
            "top_categories": {},
            "recent_transactions": []
        }

        for transaction in transactions:
            if transaction["transaction_type"] == "debit":
                summary["debit_transactions"] += 1
                summary["total_spent"] += transaction["amount"]
                category = transaction["category"]
                if category in summary["top_categories"]:
                    summary["top_categories"][category] += transaction["amount"]
                else:
                    summary["top_categories"][category] = transaction["amount"]
            elif transaction["transaction_type"] == "credit":
                summary["credit_transactions"] += 1

            # Add recent transaction details
            summary["recent_transactions"].append({
                "description": transaction["description"],
                "category": transaction["category"],
                "amount": transaction["amount"],
                "type": transaction["transaction_type"]
            })

        # Sort top categories by spending
        summary["top_categories"] = sorted(summary["top_categories"].items(), key=lambda item: item[1], reverse=True)[:3]

        return summary

    def _prepare_profile_summary(self, user_profile: Dict) -> str:
        """Prepares a concise summary of the user's profile."""
        if not user_profile:
            return "No profile information available."

        summary_parts = []

        if user_profile.get("name"):
            summary_parts.append(f"Name: {user_profile['name']}")
        if user_profile.get("age_group"):
            summary_parts.append(f"Age Group: {user_profile['age_group']}")
        if user_profile.get("income_range"):
            summary_parts.append(f"Income Range: {user_profile['income_range']}")
        if user_profile.get("financial_goals"):
            summary_parts.append(f"Financial Goal: {user_profile['financial_goals']}")
        if user_profile.get("financial_style"):
            summary_parts.append(f"Financial Style: {user_profile['financial_style']}")
        if user_profile.get("debt_status"):
            summary_parts.append(f"Debt Status: {user_profile['debt_status']}")
        if user_profile.get("investment_experience"):
            summary_parts.append(f"Investment Experience: {user_profile['investment_experience']}")

        return "; ".join(summary_parts)
    def categorize_transaction_ai(self, transaction_text: str, amount: float, merchant: str = None) -> Dict:
        system_prompt = """Categorize transactions. Return JSON:
{
  "category": "...",
  "subcategory": "...",
  "confidence": 0.0-1.0,
  "reasoning": "why"
}"""
        user_prompt = f"""Transaction: {transaction_text}, Amount: {amount}, Merchant: {merchant or "Unknown"}"""
        response = self._ask_llm(system_prompt, user_prompt, temperature=0.1)
        try:
            return json.loads(response)
        except:
            return {
                "category": "Others",
                "subcategory": "Uncategorized",
                "confidence": 0.0,
                "reasoning": "Parsing failed"
            }

    def _prepare_transaction_summary(self, transactions: List[Dict]) -> Dict:
        if not transactions:
            return {"total_transactions": 0, "categories": {}, "monthly_spending": 0}

        cat_spend = {}
        total = 0
        count = 0

        for tx in transactions:
            if tx.get("transaction_type") == "debit":
                amt = tx.get("amount", 0)
                cat = tx.get("category", "Others")
                cat_spend[cat] = cat_spend.get(cat, 0) + amt
                total += amt
                count += 1

        monthly = total / max(1, count / 30) if count > 30 else total

        return {
            "total_transactions": count,
            "total_spending": total,
            "monthly_spending": monthly,
            "categories": cat_spend,
            "top_categories": sorted(cat_spend.items(), key=lambda x: x[1], reverse=True)[:5]
        }

    def get_location_based_recommendations(self, location: str = None) -> List[Dict]:
        if not location:
            return []

        user_profile = get_user_profile(self.user_id)
        transactions = get_user_transactions(self.user_id, limit=50)

        system_prompt = """You are a location-aware financial assistant. Your task is to generate 1–2 personalized, location-based money-saving or budgeting tips in JSON format.

Analyze the following:
- User's age, income, financial goals, and financial style
- User's location
- recent spending categories (e.g., high spending on shopping, food, etc.)

Make your suggestions **personalized to the user’s lifestyle and location context**, such as:
- Recommending cheaper dining options or grocery hacks in the user's city
- Highlighting local discounts or government schemes based on their income
- Suggesting better transport or subscription alternatives available nearby

Output format:
[
  {
    "type": "dining|shopping|services|entertainment|transport",
    "title": "short title",
    "description": "actionable advice with local context and estimated savings if possible",
    "location_context": "why this advice is relevant to this location"
  }
]
Only return valid JSON. Do not include explanations or markdown.
"""

        user_prompt = f"""Location: {location}
User Profile: {json.dumps(user_profile, indent=2)}
Transaction Summary: {json.dumps(self._prepare_transaction_summary(transactions), indent=2)}"""

        response = self._ask_llm(system_prompt, user_prompt, temperature=0.3)

        try:
            return json.loads(response)
        except:
            return []
