"""
Input validation and sanitization utilities for the modular chatbot system.
"""
import re
import html
from typing import Optional
import nh3


class InputSanitizer:
    """Handles input sanitization and validation."""
    
    # Allowed HTML tags (empty list means no HTML allowed)
    ALLOWED_TAGS = []
    
    # Allowed HTML attributes
    ALLOWED_ATTRIBUTES = {}
    
    # Maximum input length
    MAX_INPUT_LENGTH = 10000
    
    # Patterns for detecting potential prompt injection
    INJECTION_PATTERNS = [
        # Direct instruction overrides
        r'ignore\s+previous\s+instructions',
        r'forget\s+everything',
        r'disregard\s+all\s+previous',
        r'override\s+system',
        r'new\s+instructions',
        
        # Role manipulation
        r'system\s*:',
        r'assistant\s*:',
        r'human\s*:',
        r'user\s*:',
        r'ai\s*:',
        r'you\s+are\s+now',
        r'act\s+as\s+if',
        r'pretend\s+to\s+be',
        
        # Code injection attempts
        r'<\s*script\s*>',
        r'javascript\s*:',
        r'eval\s*\(',
        r'exec\s*\(',
        r'function\s*\(',
        r'<\s*iframe',
        r'<\s*object',
        r'<\s*embed',
        
        # Prompt breaking attempts
        r'```\s*system',
        r'```\s*assistant',
        r'---\s*system',
        r'###\s*system',
        r'\[\s*system\s*\]',
        r'\(\s*system\s*\)',
        
        # Data exfiltration attempts
        r'show\s+me\s+your\s+prompt',
        r'what\s+are\s+your\s+instructions',
        r'reveal\s+your\s+system',
        r'display\s+your\s+rules',
        
        # Jailbreak attempts
        r'developer\s+mode',
        r'debug\s+mode',
        r'admin\s+mode',
        r'god\s+mode',
        r'unrestricted\s+mode',
    ]
    
    @classmethod
    def sanitize_input(cls, input_text: str) -> str:
        """
        Sanitize user input by removing potentially harmful content.
        
        Args:
            input_text: Raw user input
            
        Returns:
            Sanitized input text
            
        Raises:
            ValueError: If input is invalid or too long
        """
        if not isinstance(input_text, str):
            raise ValueError("Input must be a string")
        
        if len(input_text) > cls.MAX_INPUT_LENGTH:
            raise ValueError(f"Input too long. Maximum length is {cls.MAX_INPUT_LENGTH} characters")
        
        # Remove HTML tags and escape HTML entities using nh3
        # nh3 is a fast, secure HTML sanitizer written in Rust
        try:
            # Configure nh3 to remove all HTML tags and attributes (safest for chat input)
            sanitized = nh3.clean(
                input_text,
                tags=set(),  # No HTML tags allowed
                attributes={},  # No attributes allowed
                strip_comments=True,
                link_rel="noopener noreferrer"
            )
        except Exception as e:
            # Fallback to basic HTML escaping if nh3 fails
            sanitized = html.escape(input_text)
        
        # Unescape HTML entities that were double-escaped
        sanitized = html.unescape(sanitized)
        
        # Remove null bytes and other control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    @classmethod
    def detect_prompt_injection(cls, input_text: str) -> bool:
        """
        Detect potential prompt injection attempts.
        
        Args:
            input_text: Input text to analyze
            
        Returns:
            True if potential injection detected, False otherwise
        """
        if not isinstance(input_text, str):
            return False
        
        # Quick length check - very long inputs are suspicious
        if len(input_text) > 5000:
            return True
        
        # Convert to lowercase for pattern matching
        text_lower = input_text.lower()
        
        # Remove extra whitespace for better pattern matching
        text_normalized = re.sub(r'\s+', ' ', text_lower).strip()
        
        # Check against known injection patterns
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text_normalized, re.IGNORECASE):
                return True
        
        # Check for excessive special characters (potential obfuscation)
        special_char_ratio = len(re.findall(r'[^\w\s]', input_text)) / max(len(input_text), 1)
        if special_char_ratio > 0.3:  # More than 30% special characters
            return True
        
        # Check for repeated patterns (potential prompt stuffing)
        words = text_normalized.split()
        if len(words) > 10:
            word_counts = {}
            for word in words:
                if len(word) > 3:  # Only count meaningful words
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            # If any word appears more than 20% of the time, it's suspicious
            max_count = max(word_counts.values()) if word_counts else 0
            if max_count > len(words) * 0.2:
                return True
        
        # Check for base64-like patterns (potential encoded payloads)
        base64_pattern = r'[A-Za-z0-9+/]{20,}={0,2}'
        if re.search(base64_pattern, input_text):
            return True
        
        return False
    
    @classmethod
    def validate_user_id(cls, user_id: str) -> bool:
        """
        Validate user ID format.
        
        Args:
            user_id: User identifier to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(user_id, str):
            return False
        
        # User ID should be alphanumeric with optional hyphens/underscores
        pattern = r'^[a-zA-Z0-9_-]{1,50}$'
        return bool(re.match(pattern, user_id))
    
    @classmethod
    def validate_conversation_id(cls, conversation_id: str) -> bool:
        """
        Validate conversation ID format.
        
        Args:
            conversation_id: Conversation identifier to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(conversation_id, str):
            return False
        
        # Conversation ID should be alphanumeric with optional hyphens/underscores
        pattern = r'^[a-zA-Z0-9_-]{1,100}$'
        return bool(re.match(pattern, conversation_id))


class SecurityValidator:
    """Additional security validation utilities."""
    
    @staticmethod
    def validate_message_content(content: str) -> tuple[bool, Optional[str]]:
        """
        Comprehensive validation of message content.
        
        Args:
            content: Message content to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(content, str):
            return False, "Content must be a string"
        
        if not content.strip():
            return False, "Content cannot be empty"
        
        if len(content) > InputSanitizer.MAX_INPUT_LENGTH:
            return False, f"Content too long. Maximum length is {InputSanitizer.MAX_INPUT_LENGTH} characters"
        
        # Check for prompt injection
        if InputSanitizer.detect_prompt_injection(content):
            return False, "Potentially malicious content detected"
        
        return True, None
    
    @staticmethod
    def validate_request_data(message: str, user_id: str, conversation_id: str) -> tuple[bool, Optional[str]]:
        """
        Validate all request data fields.
        
        Args:
            message: User message
            user_id: User identifier
            conversation_id: Conversation identifier
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate message content
        is_valid, error = SecurityValidator.validate_message_content(message)
        if not is_valid:
            return False, f"Invalid message: {error}"
        
        # Validate user ID
        if not InputSanitizer.validate_user_id(user_id):
            return False, "Invalid user ID format"
        
        # Validate conversation ID
        if not InputSanitizer.validate_conversation_id(conversation_id):
            return False, "Invalid conversation ID format"
        
        return True, None


# Legacy functions for backward compatibility
def validate_user_id(user_id: str) -> bool:
    """Legacy function for backward compatibility."""
    return InputSanitizer.validate_user_id(user_id)


def validate_conversation_id(conversation_id: str) -> bool:
    """Legacy function for backward compatibility."""
    return InputSanitizer.validate_conversation_id(conversation_id)