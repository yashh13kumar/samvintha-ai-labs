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
from bs4 import BeautifulSoup

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailParser:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.service = None
        self.creds = None

    def authenticate(self) -> bool:
        try:
            if os.path.exists('token.json'):
                self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)

            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    self.creds = flow.run_local_server(port=0)
                    with open('token.json', 'w') as token:
                        token.write(self.creds.to_json())

            self.service = build('gmail', 'v1', credentials=self.creds)
            return True
        except Exception as e:
            st.error(f"Gmail authentication failed: {str(e)}")
            return False

    def get_financial_emails(self, max_results: int = 100) -> List[Dict]:
        if not self.service:
            return []

        try:
            financial_keywords = [
                'transaction', 'payment', 'debit', 'credit', 'bank', 'card',
                'purchase', 'withdrawal', 'deposit', 'transfer', 'bill',
                'invoice', 'receipt', 'statement', 'balance', 'amount',
                'charged', 'paid', 'refund', 'cashback', 'reward'
            ]

            query = ' OR '.join([f'subject:{keyword}' for keyword in financial_keywords])
            query += ' OR ' + ' OR '.join([f'body:{keyword}' for keyword in financial_keywords])

            messages = []
            results = self.service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages.extend(results.get('messages', []))

            while 'nextPageToken' in results and len(messages) < max_results:
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=max_results - len(messages),
                    pageToken=results['nextPageToken']
                ).execute()
                messages.extend(results.get('messages', []))

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
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()

            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

            body_raw = self.extract_email_body(message['payload'])
            body = BeautifulSoup(body_raw, 'html.parser').get_text()

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
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                data = part['body'].get('data')
                if data:
                    decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                    if mime_type == 'text/plain':
                        return decoded
                    elif mime_type == 'text/html':
                        fallback = decoded
            return fallback if 'fallback' in locals() else ''
        else:
            data = payload['body'].get('data')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')
        return ''

    def extract_transactions_from_emails(self, emails: List[Dict]) -> List[Dict]:
        from ai_agent import FinancialAgent

        agent = FinancialAgent(self.user_id)
        transactions = []

        for email in emails:
            try:
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
        return transactions

    def parse_transaction_amount(self, text: str) -> Optional[float]:
        patterns = [
            r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'INR\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:INR|Rs\.?|₹)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return float(matches[0].replace(',', ''))
                except ValueError:
                    continue
        return None

    def identify_transaction_type(self, text: str) -> str:
        text_lower = text.lower()
        if any(word in text_lower for word in ['debited', 'debit', 'purchase', 'paid', 'withdrawal', 'spent']):
            return 'debit'
        if any(word in text_lower for word in ['credited', 'credit', 'received', 'deposit', 'refund', 'cashback']):
            return 'credit'
        return 'debit'
