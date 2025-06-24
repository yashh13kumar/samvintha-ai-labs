import os
import base64
import email
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import streamlit as st
import re
from typing import List, Dict, Optional
from datetime import datetime
import json

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailParser:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.service = None
        self.creds = None
        
    def authenticate(self) -> bool:
        """Authenticate with Gmail API"""
        try:
            # Check if we have stored credentials
            if os.path.exists('token.json'):
                self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            # If there are no (valid) credentials available, let the user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # For production, you would handle this differently
                    # This is a simplified version for the demo
                    return False
            
            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=self.creds)
            return True
            
        except Exception as e:
            st.error(f"Gmail authentication failed: {str(e)}")
            return False
    
    def get_financial_emails(self, max_results: int = 100) -> List[Dict]:
        """Get emails that potentially contain financial information"""
        if not self.service:
            return []
        
        try:
            # Define financial keywords for filtering
            financial_keywords = [
                'transaction', 'payment', 'debit', 'credit', 'bank', 'card',
                'purchase', 'withdrawal', 'deposit', 'transfer', 'bill',
                'invoice', 'receipt', 'statement', 'balance', 'amount',
                'charged', 'paid', 'refund', 'cashback', 'reward'
            ]
            
            # Build search query
            query = ' OR '.join([f'subject:{keyword}' for keyword in financial_keywords])
            query += ' OR ' + ' OR '.join([f'body:{keyword}' for keyword in financial_keywords])
            
            # Search for emails
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            financial_emails = []
            for message in messages:
                email_data = self.get_email_content(message['id'])
                if email_data:
                    financial_emails.append(email_data)
            
            return financial_emails
            
        except HttpError as error:
            st.error(f"An error occurred: {error}")
            return []
    
    def get_email_content(self, message_id: str) -> Optional[Dict]:
        """Get content of a specific email"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = self.extract_email_body(message['payload'])
            
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'raw_message': message
            }
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
    
    def extract_email_body(self, payload) -> str:
        """Extract email body from payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
            elif payload['mimeType'] == 'text/html':
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    def extract_transactions_from_emails(self, emails: List[Dict]) -> List[Dict]:
        """Extract transaction data from emails using AI"""
        from ai_agent import FinancialAgent
        
        agent = FinancialAgent(self.user_id)
        transactions = []
        
        for email in emails:
            try:
                # Use AI to extract transaction information
                transaction_data = agent.extract_transaction_from_text(
                    email['body'],
                    source='email',
                    metadata={
                        'subject': email['subject'],
                        'sender': email['sender'],
                        'date': email['date']
                    }
                )
                
                if transaction_data:
                    transactions.append(transaction_data)
                    
            except Exception as e:
                print(f"Error processing email {email['id']}: {str(e)}")
                continue
        
        return transactions
    
    def parse_transaction_amount(self, text: str) -> Optional[float]:
        """Parse transaction amount from text"""
        # Pattern for currency amounts
        patterns = [
            r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Indian Rupees
            r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # US Dollars
            r'Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Rupees
            r'INR\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # INR
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:INR|Rs\.?|₹)',  # Amount before currency
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Clean and convert to float
                amount_str = matches[0].replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None
    
    def identify_transaction_type(self, text: str) -> str:
        """Identify transaction type from text"""
        text_lower = text.lower()
        
        # Debit indicators
        if any(word in text_lower for word in ['debited', 'debit', 'purchase', 'paid', 'withdrawal', 'spent']):
            return 'debit'
        
        # Credit indicators
        if any(word in text_lower for word in ['credited', 'credit', 'received', 'deposit', 'refund', 'cashback']):
            return 'credit'
        
        # Default to debit if uncertain
        return 'debit'
    
    def get_oauth_url(self) -> str:
        """Get OAuth URL for Gmail authentication"""
        try:
            # This would be implemented for production OAuth flow
            # For now, return placeholder
            return "https://accounts.google.com/oauth/authorize?..."
        except Exception as e:
            return ""
    
    def process_oauth_callback(self, auth_code: str) -> bool:
        """Process OAuth callback"""
        try:
            # This would be implemented for production OAuth flow
            # For now, return success
            return True
        except Exception as e:
            return False