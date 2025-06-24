import re
from datetime import datetime, date
from typing import Union, Optional, List, Dict, Any
import streamlit as st
import pandas as pd

def format_currency(amount: float, currency: str = "₹") -> str:
    """Format amount as currency with proper formatting"""
    if amount == 0:
        return f"{currency}0"
    
    # Handle negative amounts
    if amount < 0:
        return f"-{currency}{abs(amount):,.2f}"
    
    # Indian number formatting (lakhs and crores)
    if amount >= 10000000:  # 1 crore
        return f"{currency}{amount/10000000:.2f}Cr"
    elif amount >= 100000:  # 1 lakh
        return f"{currency}{amount/100000:.2f}L"
    elif amount >= 1000:
        return f"{currency}{amount:,.2f}"
    else:
        return f"{currency}{amount:.2f}"

def format_date(date_input: Union[str, datetime, date], format_type: str = "short") -> str:
    """Format date for display"""
    if not date_input:
        return "Unknown"
    
    try:
        # Convert string to datetime if needed
        if isinstance(date_input, str):
            # Try different date formats
            date_formats = [
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M:%S',
                '%d-%m-%Y',
                '%d/%m/%Y',
                '%Y/%m/%d'
            ]
            
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_input, fmt)
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                return date_input  # Return original if parsing fails
            
            date_input = parsed_date
        
        # Format based on type
        if format_type == "short":
            return date_input.strftime("%b %d")
        elif format_type == "medium":
            return date_input.strftime("%b %d, %Y")
        elif format_type == "long":
            return date_input.strftime("%B %d, %Y")
        elif format_type == "relative":
            return format_relative_date(date_input)
        else:
            return date_input.strftime("%Y-%m-%d")
    
    except Exception as e:
        return "Invalid Date"

def format_relative_date(date_input: datetime) -> str:
    """Format date relative to current time"""
    now = datetime.now()
    diff = now - date_input
    
    if diff.days == 0:
        return "Today"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days} days ago"
    elif diff.days < 30:
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif diff.days < 365:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"

def validate_amount(amount: str) -> tuple[bool, float]:
    """Validate and parse amount string"""
    if not amount or not amount.strip():
        return False, 0.0
    
    # Remove currency symbols and spaces
    clean_amount = re.sub(r'[₹$,\s]', '', amount.strip())
    
    try:
        parsed_amount = float(clean_amount)
        if parsed_amount < 0:
            return False, 0.0
        return True, parsed_amount
    except ValueError:
        return False, 0.0

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate Indian phone number format"""
    if not phone:
        return False
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check for valid Indian mobile number patterns
    if len(digits) == 10 and digits[0] in '6789':
        return True
    elif len(digits) == 12 and digits[:2] == '91' and digits[2] in '6789':
        return True
    elif len(digits) == 13 and digits[:3] == '+91' and digits[3] in '6789':
        return True
    
    return False

def calculate_percentage_change(current: float, previous: float) -> float:
    """Calculate percentage change between two values"""
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    
    return ((current - previous) / previous) * 100

def clean_text(text: str) -> str:
    """Clean and normalize text input"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters that might cause issues
    text = re.sub(r'[^\w\s\-.,!?@#$%^&*()+={}[\]:;"\'<>]', '', text)
    
    return text.strip()

def extract_numbers(text: str) -> List[float]:
    """Extract all numbers from text"""
    if not text:
        return []
    
    # Pattern to match numbers (including decimals and with commas)
    pattern = r'\d+(?:,\d{3})*(?:\.\d{2})?'
    matches = re.findall(pattern, text)
    
    numbers = []
    for match in matches:
        try:
            # Remove commas and convert to float
            clean_number = match.replace(',', '')
            numbers.append(float(clean_number))
        except ValueError:
            continue
    
    return numbers

def categorize_merchant(merchant_name: str) -> str:
    """Categorize merchant based on name"""
    if not merchant_name:
        return "Others"
    
    merchant_lower = merchant_name.lower()
    
    # Define category mappings
    categories = {
        'Food & Dining': [
            'restaurant', 'cafe', 'food', 'dining', 'pizza', 'burger', 'swiggy', 
            'zomato', 'dominos', 'kfc', 'mcdonalds', 'subway', 'starbucks'
        ],
        'Shopping': [
            'amazon', 'flipkart', 'myntra', 'jabong', 'shopping', 'mall', 'store',
            'retail', 'clothing', 'fashion', 'electronics', 'mobile', 'laptop'
        ],
        'Transportation': [
            'uber', 'ola', 'taxi', 'auto', 'metro', 'bus', 'train', 'flight',
            'airport', 'railway', 'transport', 'fuel', 'petrol', 'diesel'
        ],
        'Utilities': [
            'electricity', 'power', 'water', 'gas', 'internet', 'broadband',
            'mobile', 'recharge', 'bill', 'utility', 'telecom', 'phone'
        ],
        'Healthcare': [
            'hospital', 'clinic', 'doctor', 'medical', 'pharmacy', 'medicine',
            'health', 'dental', 'lab', 'diagnostic', 'apollo', 'fortis'
        ],
        'Entertainment': [
            'movie', 'cinema', 'theatre', 'bookmyshow', 'entertainment',
            'game', 'sports', 'gym', 'fitness', 'netflix', 'spotify'
        ],
        'Groceries': [
            'grocery', 'supermarket', 'bigbasket', 'grofers', 'reliance',
            'dmart', 'more', 'food', 'vegetables', 'fruits', 'market'
        ]
    }
    
    # Check each category
    for category, keywords in categories.items():
        if any(keyword in merchant_lower for keyword in keywords):
            return category
    
    return "Others"

def generate_transaction_id() -> str:
    """Generate a unique transaction ID"""
    import uuid
    return str(uuid.uuid4())[:8].upper()

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default

def format_large_number(number: float) -> str:
    """Format large numbers with appropriate suffixes"""
    if abs(number) >= 10**9:
        return f"{number/10**9:.1f}B"
    elif abs(number) >= 10**6:
        return f"{number/10**6:.1f}M"
    elif abs(number) >= 10**3:
        return f"{number/10**3:.1f}K"
    else:
        return f"{number:.1f}"

def create_summary_stats(data: List[Dict], amount_field: str = 'amount') -> Dict:
    """Create summary statistics from transaction data"""
    if not data:
        return {
            'count': 0,
            'total': 0,
            'average': 0,
            'median': 0,
            'min': 0,
            'max': 0
        }
    
    amounts = [float(item.get(amount_field, 0)) for item in data if item.get(amount_field)]
    
    if not amounts:
        return {
            'count': len(data),
            'total': 0,
            'average': 0,
            'median': 0,
            'min': 0,
            'max': 0
        }
    
    return {
        'count': len(amounts),
        'total': sum(amounts),
        'average': sum(amounts) / len(amounts),
        'median': sorted(amounts)[len(amounts) // 2],
        'min': min(amounts),
        'max': max(amounts)
    }

def filter_recent_data(data: List[Dict], date_field: str = 'date', days: int = 30) -> List[Dict]:
    """Filter data to include only recent entries"""
    if not data:
        return []
    
    cutoff_date = datetime.now() - pd.Timedelta(days=days)
    
    filtered_data = []
    for item in data:
        if date_field in item:
            try:
                item_date = pd.to_datetime(item[date_field])
                if item_date >= cutoff_date:
                    filtered_data.append(item)
            except (ValueError, TypeError):
                continue
    
    return filtered_data

def group_by_category(transactions: List[Dict], category_field: str = 'category') -> Dict[str, List[Dict]]:
    """Group transactions by category"""
    grouped = {}
    
    for transaction in transactions:
        category = transaction.get(category_field, 'Others')
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(transaction)
    
    return grouped

def calculate_spending_trend(transactions: List[Dict], days: int = 30) -> Dict:
    """Calculate spending trend over specified period"""
    if not transactions:
        return {'trend': 'stable', 'change_percent': 0, 'current_spending': 0, 'previous_spending': 0}
    
    # Filter debit transactions
    debit_transactions = [t for t in transactions if t.get('transaction_type') == 'debit']
    
    if not debit_transactions:
        return {'trend': 'stable', 'change_percent': 0, 'current_spending': 0, 'previous_spending': 0}
    
    now = datetime.now()
    current_period_start = now - pd.Timedelta(days=days)
    previous_period_start = now - pd.Timedelta(days=days*2)
    
    current_spending = 0
    previous_spending = 0
    
    for transaction in debit_transactions:
        try:
            trans_date = pd.to_datetime(transaction.get('date'))
            amount = float(transaction.get('amount', 0))
            
            if trans_date >= current_period_start:
                current_spending += amount
            elif trans_date >= previous_period_start:
                previous_spending += amount
        except (ValueError, TypeError):
            continue
    
    change_percent = calculate_percentage_change(current_spending, previous_spending)
    
    if change_percent > 10:
        trend = 'increasing'
    elif change_percent < -10:
        trend = 'decreasing'
    else:
        trend = 'stable'
    
    return {
        'trend': trend,
        'change_percent': change_percent,
        'current_spending': current_spending,
        'previous_spending': previous_spending
    }

def export_to_csv(data: List[Dict], filename: str = None) -> str:
    """Export data to CSV format"""
    if not data:
        return ""
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False)

def import_from_csv(csv_content: str) -> List[Dict]:
    """Import data from CSV content"""
    try:
        from io import StringIO
        df = pd.read_csv(StringIO(csv_content))
        return df.to_dict('records')
    except Exception as e:
        st.error(f"Error importing CSV: {str(e)}")
        return []

def highlight_keywords(text: str, keywords: List[str], color: str = "#ffeb3b") -> str:
    """Highlight keywords in text for display"""
    if not text or not keywords:
        return text
    
    highlighted_text = text
    for keyword in keywords:
        if keyword.lower() in text.lower():
            highlighted_text = highlighted_text.replace(
                keyword,
                f'<mark style="background-color: {color};">{keyword}</mark>'
            )
    
    return highlighted_text

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def get_financial_year_dates(year: int = None) -> tuple[datetime, datetime]:
    """Get financial year start and end dates (April 1 to March 31 for India)"""
    if year is None:
        current_date = datetime.now()
        if current_date.month >= 4:
            year = current_date.year
        else:
            year = current_date.year - 1
    
    start_date = datetime(year, 4, 1)
    end_date = datetime(year + 1, 3, 31)
    
    return start_date, end_date

def is_business_day(date_input: Union[datetime, date]) -> bool:
    """Check if given date is a business day (Monday-Friday)"""
    if isinstance(date_input, str):
        date_input = datetime.strptime(date_input, '%Y-%m-%d').date()
    elif isinstance(date_input, datetime):
        date_input = date_input.date()
    
    return date_input.weekday() < 5  # Monday is 0, Sunday is 6

def get_month_name(month_number: int) -> str:
    """Get month name from month number"""
    months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    
    if 1 <= month_number <= 12:
        return months[month_number - 1]
    else:
        return 'Unknown'

def calculate_age_from_age_group(age_group: str) -> int:
    """Calculate approximate age from age group"""
    age_mapping = {
        '<25': 22,
        '25–35': 30,
        '35–50': 42,
        '>50': 55
    }
    
    return age_mapping.get(age_group, 30)

def format_confidence_score(score: float) -> str:
    """Format AI confidence score for display"""
    if score >= 0.9:
        return f"High ({score:.0%})"
    elif score >= 0.7:
        return f"Medium ({score:.0%})"
    elif score >= 0.5:
        return f"Low ({score:.0%})"
    else:
        return f"Very Low ({score:.0%})"

def create_color_palette(n_colors: int) -> List[str]:
    """Create a color palette with n colors"""
    import colorsys
    
    colors = []
    for i in range(n_colors):
        hue = i / n_colors
        rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            int(rgb[0] * 255),
            int(rgb[1] * 255),
            int(rgb[2] * 255)
        )
        colors.append(hex_color)
    
    return colors