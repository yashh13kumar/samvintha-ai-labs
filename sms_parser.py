import re
from typing import List, Dict, Optional
from datetime import datetime
import streamlit as st
from database import save_transaction

class SMSParser:
    def __init__(self, user_id: int):
        self.user_id = user_id
        
        # Common SMS patterns for different banks and services
        self.bank_patterns = {
            'sbi': {
                'debit': r'Dear Customer, Rs\.(\d+(?:\.\d{2})?).* debited.*A/c.*(\d{4}).*on (\d{2}-\d{2}-\d{4})',
                'credit': r'Dear Customer, Rs\.(\d+(?:\.\d{2})?).* credited.*A/c.*(\d{4}).*on (\d{2}-\d{2}-\d{4})'
            },
            'hdfc': {
                'debit': r'Rs\.(\d+(?:\.\d{2})?).* debited.*A/C.*(\d{4}).*on (\d{2}-\d{2}-\d{4})',
                'credit': r'Rs\.(\d+(?:\.\d{2})?).* credited.*A/C.*(\d{4}).*on (\d{2}-\d{2}-\d{4})'
            },
            'icici': {
                'debit': r'Rs\.(\d+(?:\.\d{2})?).* debited.*card.*(\d{4}).*on (\d{2}-\d{2}-\d{4})',
                'credit': r'Rs\.(\d+(?:\.\d{2})?).* credited.*card.*(\d{4}).*on (\d{2}-\d{2}-\d{4})'
            },
            'axis': {
                'debit': r'Rs\.(\d+(?:\.\d{2})?).* debited.*card.*(\d{4}).*on (\d{2}-\d{2}-\d{4})',
                'credit': r'Rs\.(\d+(?:\.\d{2})?).* credited.*card.*(\d{4}).*on (\d{2}-\d{2}-\d{4})'
            },
            'paytm': {
                'debit': r'Rs\.(\d+(?:\.\d{2})?).* debited.*Paytm.*on (\d{2}-\d{2}-\d{4})',
                'credit': r'Rs\.(\d+(?:\.\d{2})?).* added.*Paytm.*on (\d{2}-\d{2}-\d{4})'
            },
            'phonepe': {
                'debit': r'Rs\.(\d+(?:\.\d{2})?).* debited.*PhonePe.*on (\d{2}-\d{2}-\d{4})',
                'credit': r'Rs\.(\d+(?:\.\d{2})?).* credited.*PhonePe.*on (\d{2}-\d{2}-\d{4})'
            },
            'gpay': {
                'debit': r'Rs\.(\d+(?:\.\d{2})?).* paid.*Google Pay.*on (\d{2}-\d{2}-\d{4})',
                'credit': r'Rs\.(\d+(?:\.\d{2})?).* received.*Google Pay.*on (\d{2}-\d{2}-\d{4})'
            }
        }
        
        # Merchant identification patterns
        self.merchant_patterns = {
            'amazon': r'(?:Amazon|AMAZON|amazon)',
            'flipkart': r'(?:Flipkart|FLIPKART|flipkart)',
            'swiggy': r'(?:Swiggy|SWIGGY|swiggy)',
            'zomato': r'(?:Zomato|ZOMATO|zomato)',
            'uber': r'(?:Uber|UBER|uber)',
            'ola': r'(?:Ola|OLA|ola)',
            'myntra': r'(?:Myntra|MYNTRA|myntra)',
            'bigbasket': r'(?:BigBasket|BIGBASKET|bigbasket)',
            'grofers': r'(?:Grofers|GROFERS|grofers)',
            'bookmyshow': r'(?:BookMyShow|BOOKMYSHOW|bookmyshow)',
            'makemytrip': r'(?:MakeMyTrip|MAKEMYTRIP|makemytrip)',
            'petrol': r'(?:PETROL|petrol|Petrol|FUEL|fuel|Fuel)',
            'atm': r'(?:ATM|atm|Atm)',
            'electricity': r'(?:ELECTRICITY|electricity|Electricity|power|POWER)',
            'mobile': r'(?:MOBILE|mobile|Mobile|recharge|RECHARGE)'
        }
    
    def parse_sms_messages(self, sms_messages: List[Dict]) -> List[Dict]:
        """Parse SMS messages to extract transaction data"""
        transactions = []
        
        for sms in sms_messages:
            try:
                transaction = self.extract_transaction_from_sms(sms)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                print(f"Error parsing SMS: {str(e)}")
                continue
        
        return transactions
    
    def extract_transaction_from_sms(self, sms: Dict) -> Optional[Dict]:
        """Extract transaction data from a single SMS"""
        message = sms.get('message', '').strip()
        sender = sms.get('sender', '').strip()
        timestamp = sms.get('timestamp', datetime.now())
        
        # Skip if message is empty or too short
        if len(message) < 10:
            return None
        
        # Check if this looks like a financial SMS
        if not self.is_financial_sms(message):
            return None
        
        # Try to extract transaction using bank patterns
        transaction_data = self.extract_using_bank_patterns(message, sender)
        
        if not transaction_data:
            # Fallback to AI-based extraction
            transaction_data = self.extract_using_ai(message, sender)
        
        if transaction_data:
            # Add common fields
            transaction_data.update({
                'source': 'sms',
                'raw_text': message,
                'timestamp': timestamp,
                'sender': sender
            })
            
            # Identify merchant
            merchant = self.identify_merchant(message)
            if merchant:
                transaction_data['merchant'] = merchant
            
            # Categorize transaction
            category = self.categorize_transaction(message, merchant)
            transaction_data['category'] = category
            
            return transaction_data
        
        return None
    
    def is_financial_sms(self, message: str) -> bool:
        """Check if SMS contains financial information"""
        financial_keywords = [
            'rs.', 'rs ', 'inr', 'rupees', 'amount', 'balance', 'debited', 'credited',
            'paid', 'received', 'transaction', 'purchase', 'payment', 'debit', 'credit',
            'withdrawal', 'deposit', 'transfer', 'account', 'card', 'bank', 'atm',
            'upi', 'paytm', 'phonepe', 'gpay', 'wallet'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in financial_keywords)
    
    def extract_using_bank_patterns(self, message: str, sender: str) -> Optional[Dict]:
        """Extract transaction using predefined bank patterns"""
        for bank, patterns in self.bank_patterns.items():
            if bank.lower() in sender.lower() or bank.upper() in sender.upper():
                for transaction_type, pattern in patterns.items():
                    match = re.search(pattern, message, re.IGNORECASE)
                    if match:
                        groups = match.groups()
                        if len(groups) >= 2:
                            amount = float(groups[0])
                            account_digits = groups[1] if len(groups) > 1 else ''
                            date_str = groups[2] if len(groups) > 2 else ''
                            
                            return {
                                'transaction_type': transaction_type,
                                'amount': amount,
                                'account_digits': account_digits,
                                'date': self.parse_date(date_str) if date_str else datetime.now().date(),
                                'bank': bank,
                                'ai_confidence': 0.9
                            }
        
        return None
    
    def extract_using_ai(self, message: str, sender: str) -> Optional[Dict]:
        """Extract transaction using AI when patterns fail"""
        from ai_agent import FinancialAgent
        
        try:
            agent = FinancialAgent(self.user_id)
            return agent.extract_transaction_from_text(
                message,
                source='sms',
                metadata={'sender': sender}
            )
        except Exception as e:
            print(f"AI extraction failed: {str(e)}")
            return None
    
    def identify_merchant(self, message: str) -> Optional[str]:
        """Identify merchant from message"""
        for merchant, pattern in self.merchant_patterns.items():
            if re.search(pattern, message, re.IGNORECASE):
                return merchant
        
        # Try to extract merchant from common patterns
        merchant_patterns = [
            r'at (.+?) on',
            r'to (.+?) on',
            r'from (.+?) on',
            r'paid to (.+?) via',
            r'sent to (.+?) via'
        ]
        
        for pattern in merchant_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                merchant = match.group(1).strip()
                if len(merchant) > 3 and len(merchant) < 30:
                    return merchant
        
        return None
    
    def categorize_transaction(self, message: str, merchant: str = None) -> str:
        """Categorize transaction based on message content and merchant"""
        message_lower = message.lower()
        
        # Merchant-based categorization
        if merchant:
            merchant_categories = {
                'amazon': 'Shopping',
                'flipkart': 'Shopping',
                'myntra': 'Shopping',
                'swiggy': 'Food & Dining',
                'zomato': 'Food & Dining',
                'uber': 'Transportation',
                'ola': 'Transportation',
                'bigbasket': 'Groceries',
                'grofers': 'Groceries',
                'bookmyshow': 'Entertainment',
                'makemytrip': 'Travel',
                'petrol': 'Fuel',
                'electricity': 'Utilities',
                'mobile': 'Utilities'
            }
            
            if merchant in merchant_categories:
                return merchant_categories[merchant]
        
        # Keyword-based categorization
        category_keywords = {
            'Food & Dining': ['restaurant', 'food', 'dining', 'cafe', 'hotel', 'swiggy', 'zomato'],
            'Shopping': ['shopping', 'store', 'mall', 'purchase', 'amazon', 'flipkart', 'myntra'],
            'Transportation': ['taxi', 'uber', 'ola', 'metro', 'bus', 'petrol', 'fuel'],
            'Entertainment': ['movie', 'cinema', 'bookmyshow', 'entertainment', 'game'],
            'Utilities': ['electricity', 'water', 'gas', 'internet', 'mobile', 'recharge'],
            'Healthcare': ['hospital', 'medical', 'pharmacy', 'doctor', 'clinic'],
            'ATM': ['atm', 'cash withdrawal'],
            'Transfer': ['transfer', 'sent', 'received', 'upi', 'neft', 'imps'],
            'Investment': ['mutual fund', 'sip', 'investment', 'stock', 'share'],
            'Insurance': ['insurance', 'premium', 'policy']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return category
        
        return 'Others'
    
    def parse_date(self, date_str: str) -> datetime.date:
        """Parse date string to datetime.date"""
        try:
            # Common date formats in SMS
            formats = ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%y', '%d/%m/%y']
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            
            # If no format matches, return current date
            return datetime.now().date()
            
        except Exception:
            return datetime.now().date()
    
    def get_sample_sms_data(self) -> List[Dict]:
        """Get sample SMS data for testing"""
        return [
            {
                'sender': 'VM-SBIINB',
                'message': 'Dear Customer, Rs.1500.00 debited from A/c No.XXXX4567 on 19-06-2025 at Amazon Pay. Avl Bal: Rs.25000.00',
                'timestamp': datetime.now()
            },
            {
                'sender': 'VM-HDFCBK',
                'message': 'Rs.850.00 debited from A/C No.XXXX1234 on 19-06-2025 for Swiggy transaction. Avl Bal: Rs.12000.00',
                'timestamp': datetime.now()
            },
            {
                'sender': 'PAYTM',
                'message': 'Rs.300.00 debited from Paytm Wallet for Zomato order on 19-06-2025. Txn ID: 123456789',
                'timestamp': datetime.now()
            }
        ]
    
    def simulate_sms_parsing(self) -> List[Dict]:
        """Simulate SMS parsing with sample data"""
        sample_sms = self.get_sample_sms_data()
        return self.parse_sms_messages(sample_sms)