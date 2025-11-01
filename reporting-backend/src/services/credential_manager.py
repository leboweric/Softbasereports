"""
Credential Manager Service
Handles encryption and decryption of sensitive credentials (database passwords)
"""

import os
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

class CredentialManager:
    """
    Manages encryption and decryption of database credentials.
    Uses Fernet symmetric encryption (AES 128 in CBC mode).
    """
    
    def __init__(self):
        """Initialize the credential manager with the encryption key from environment."""
        encryption_key = os.getenv('CREDENTIAL_ENCRYPTION_KEY')
        
        if not encryption_key:
            raise ValueError(
                "CREDENTIAL_ENCRYPTION_KEY environment variable is not set. "
                "Generate one using: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
            )
        
        try:
            self.cipher = Fernet(encryption_key.encode())
            logger.info("CredentialManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CredentialManager: {str(e)}")
            raise ValueError(f"Invalid CREDENTIAL_ENCRYPTION_KEY: {str(e)}")
    
    def encrypt_password(self, plaintext_password: str) -> str:
        """
        Encrypt a plaintext password.
        
        Args:
            plaintext_password: The password to encrypt
            
        Returns:
            The encrypted password as a base64-encoded string
            
        Raises:
            ValueError: If the password is empty or None
        """
        if not plaintext_password:
            raise ValueError("Password cannot be empty")
        
        try:
            encrypted = self.cipher.encrypt(plaintext_password.encode())
            encrypted_str = encrypted.decode()
            logger.info("Password encrypted successfully")
            return encrypted_str
        except Exception as e:
            logger.error(f"Failed to encrypt password: {str(e)}")
            raise
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """
        Decrypt an encrypted password.
        
        Args:
            encrypted_password: The encrypted password (base64-encoded string)
            
        Returns:
            The decrypted plaintext password
            
        Raises:
            ValueError: If the encrypted password is invalid or cannot be decrypted
        """
        if not encrypted_password:
            raise ValueError("Encrypted password cannot be empty")
        
        try:
            decrypted = self.cipher.decrypt(encrypted_password.encode())
            plaintext = decrypted.decode()
            # Never log the decrypted password!
            logger.info("Password decrypted successfully")
            return plaintext
        except InvalidToken:
            logger.error("Failed to decrypt password: Invalid token (wrong key or corrupted data)")
            raise ValueError("Failed to decrypt password: Invalid encryption key or corrupted data")
        except Exception as e:
            logger.error(f"Failed to decrypt password: {str(e)}")
            raise

# Create a singleton instance
_credential_manager = None

def get_credential_manager() -> CredentialManager:
    """
    Get the singleton instance of CredentialManager.
    Creates it if it doesn't exist.
    """
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager