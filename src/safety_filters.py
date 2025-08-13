"""
Safety filters for WingmanMatch Connell Barrett coaching
Implements PII protection and respectful guidance enforcement
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SafetyCheckResult:
    """Result of safety check with details"""
    is_safe: bool
    blocked_content: List[str]
    safety_message: Optional[str]
    severity: str  # 'low', 'medium', 'high'

class SafetyFilters:
    """Comprehensive safety filtering for dating confidence coaching"""
    
    def __init__(self):
        self.pii_patterns = self._init_pii_patterns()
        self.toxic_patterns = self._init_toxic_patterns()
        self.pickup_patterns = self._init_pickup_patterns()
    
    def _init_pii_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize PII detection patterns"""
        return {
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'address': re.compile(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)\b', re.IGNORECASE),
            'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
        }
    
    def _init_toxic_patterns(self) -> List[re.Pattern]:
        """Initialize toxic masculinity detection patterns"""
        toxic_phrases = [
            r'\b(?:alpha|beta)\s*male\b',
            r'\bnegging\b',
            r'\bhypergamy\b',
            r'\bincel\b',
            r'\bmgtow\b',
            r'\bred\s*pill\b',
            r'\bblack\s*pill\b',
            r'\bfemoids?\b',
            r'\broasties?\b',
            r'\bsimp\b',
            r'\bcuck\b',
            r'\bsoy\s*boy\b',
            r'\bbeta\s*bux\b',
            r'\bchad\b',
            r'\bstacy\b',
            r'\bwomen\s+are\s+(?:all|only)\b',
            r'\bgirls?\s+(?:owe|deserve)\b',
            r'\bmanipulat[ei]\b.*\bwomen\b',
            r'\btrick\b.*\binto\b',
            r'\bforce\b.*\binto\b'
        ]
        return [re.compile(pattern, re.IGNORECASE) for pattern in toxic_phrases]
    
    def _init_pickup_patterns(self) -> List[re.Pattern]:
        """Initialize pickup artist tactic detection patterns"""
        pickup_phrases = [
            r'\bpickup\s*artist\b',
            r'\bpua\b',
            r'\bgame\b.*\bwomen\b',
            r'\bfield\s*report\b',
            r'\bapproach\s*anxiety\b.*\bpush\s*through\b',
            r'\bescalat[ei]\b.*\bphysical\b',
            r'\bkino\b',
            r'\blast\s*minute\s*resistance\b',
            r'\blmr\b',
            r'\banti\s*slut\s*defense\b',
            r'\basd\b',
            r'\bshit\s*test\b',
            r'\bcomfort\s*test\b',
            r'\bioi\b',
            r'\bindicators?\s*of\s*interest\b',
            r'\bnumber\s*close\b',
            r'\bk?\s*close\b',
            r'\bf?\s*close\b'
        ]
        return [re.compile(pattern, re.IGNORECASE) for pattern in pickup_phrases]
    
    def check_message_safety(self, message: str, user_id: str = None) -> SafetyCheckResult:
        """
        Comprehensive safety check for user messages
        
        Args:
            message: User message to check
            user_id: User ID for logging
            
        Returns:
            SafetyCheckResult with safety status and details
        """
        blocked_content = []
        severity = 'low'
        
        # Check for PII
        pii_found = self._detect_pii(message)
        if pii_found:
            blocked_content.extend([f"PII: {pii_type}" for pii_type in pii_found])
            severity = 'high'
            logger.warning(f"PII detected in message from user {user_id}: {pii_found}")
        
        # Check for toxic masculinity patterns
        toxic_found = self._detect_toxic_content(message)
        if toxic_found:
            blocked_content.extend([f"Toxic content: {pattern}" for pattern in toxic_found])
            severity = 'high'
            logger.warning(f"Toxic content detected from user {user_id}: {toxic_found}")
        
        # Check for pickup artist tactics
        pickup_found = self._detect_pickup_tactics(message)
        if pickup_found:
            blocked_content.extend([f"Pickup tactics: {pattern}" for pattern in pickup_found])
            severity = 'medium'
            logger.info(f"Pickup tactics detected from user {user_id}: {pickup_found}")
        
        # Determine if message is safe
        is_safe = len(blocked_content) == 0
        safety_message = None
        
        if not is_safe:
            safety_message = self._generate_safety_message(blocked_content, severity)
        
        return SafetyCheckResult(
            is_safe=is_safe,
            blocked_content=blocked_content,
            safety_message=safety_message,
            severity=severity
        )
    
    def check_response_safety(self, response: str) -> SafetyCheckResult:
        """
        Check AI response for safety before sending to user
        
        Args:
            response: AI-generated response to check
            
        Returns:
            SafetyCheckResult with safety status
        """
        blocked_content = []
        severity = 'low'
        
        # Check for accidentally leaked PII patterns
        pii_found = self._detect_pii(response)
        if pii_found:
            blocked_content.extend([f"Response PII: {pii_type}" for pii_type in pii_found])
            severity = 'high'
            logger.error(f"AI response contains PII: {pii_found}")
        
        # Check for toxic advice
        toxic_found = self._detect_toxic_content(response)
        if toxic_found:
            blocked_content.extend([f"Toxic advice: {pattern}" for pattern in toxic_found])
            severity = 'high'
            logger.error(f"AI response contains toxic content: {toxic_found}")
        
        # Check for pickup tactics
        pickup_found = self._detect_pickup_tactics(response)
        if pickup_found:
            blocked_content.extend([f"Pickup advice: {pattern}" for pattern in pickup_found])
            severity = 'high'
            logger.error(f"AI response contains pickup tactics: {pickup_found}")
        
        is_safe = len(blocked_content) == 0
        safety_message = "Response blocked due to safety concerns" if not is_safe else None
        
        return SafetyCheckResult(
            is_safe=is_safe,
            blocked_content=blocked_content,
            safety_message=safety_message,
            severity=severity
        )
    
    def _detect_pii(self, text: str) -> List[str]:
        """Detect personal identifiable information"""
        found_pii = []
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(text):
                found_pii.append(pii_type)
        return found_pii
    
    def _detect_toxic_content(self, text: str) -> List[str]:
        """Detect toxic masculinity patterns"""
        found_patterns = []
        for pattern in self.toxic_patterns:
            match = pattern.search(text)
            if match:
                found_patterns.append(match.group(0))
        return found_patterns
    
    def _detect_pickup_tactics(self, text: str) -> List[str]:
        """Detect pickup artist tactics"""
        found_patterns = []
        for pattern in self.pickup_patterns:
            match = pattern.search(text)
            if match:
                found_patterns.append(match.group(0))
        return found_patterns
    
    def _generate_safety_message(self, blocked_content: List[str], severity: str) -> str:
        """Generate appropriate safety message for blocked content"""
        
        if any("PII" in item for item in blocked_content):
            return """I can't process messages containing personal information like phone numbers, emails, or addresses for your privacy and safety. 

Let's focus on building your confidence in a way that keeps your personal details secure."""
        
        if any("Toxic content" in item for item in blocked_content):
            return """I'm here to help you build genuine confidence and authentic connections with women. That means focusing on respect, personal growth, and becoming the best version of yourself.

Let's talk about building real confidence that comes from within - that's what attracts quality people."""
        
        if any("Pickup tactics" in item for item in blocked_content):
            return """I don't teach pickup artist tactics or manipulation strategies. Instead, I help you build authentic confidence and learn to connect with women through genuine conversation and respect.

Real confidence comes from being comfortable being yourself - let's work on that together."""
        
        return "Let's keep our conversation focused on building authentic confidence and respectful approaches to dating."
    
    def sanitize_message(self, message: str) -> str:
        """
        Sanitize message by removing/masking unsafe content
        
        Args:
            message: Message to sanitize
            
        Returns:
            Sanitized message with PII masked
        """
        sanitized = message
        
        # Mask PII patterns
        for pii_type, pattern in self.pii_patterns.items():
            if pii_type == 'phone':
                sanitized = pattern.sub('[PHONE_NUMBER]', sanitized)
            elif pii_type == 'email':
                sanitized = pattern.sub('[EMAIL_ADDRESS]', sanitized)
            elif pii_type == 'address':
                sanitized = pattern.sub('[ADDRESS]', sanitized)
            elif pii_type == 'ssn':
                sanitized = pattern.sub('[SSN]', sanitized)
            elif pii_type == 'credit_card':
                sanitized = pattern.sub('[CREDIT_CARD]', sanitized)
        
        return sanitized

# Global safety filter instance
safety_filters = SafetyFilters()

def check_message_safety(message: str, user_id: str = None) -> SafetyCheckResult:
    """Convenience function for message safety checking"""
    return safety_filters.check_message_safety(message, user_id)

def check_response_safety(response: str) -> SafetyCheckResult:
    """Convenience function for response safety checking"""
    return safety_filters.check_response_safety(response)

def sanitize_message(message: str) -> str:
    """Convenience function for message sanitization"""
    return safety_filters.sanitize_message(message)