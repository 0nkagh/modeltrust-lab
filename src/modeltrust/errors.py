"""
Exceptions for ModelTrust Lab.

Exit code mapping:
0: Success
1: Unexpected internal error
2: Usage error (argparse)
3: Not implemented yet
4: Input or validation error (schema fail, file not found, etc.)
"""

class ModelTrustError(Exception):
    """Base exception for all ModelTrust Lab errors."""
    pass

class InputError(ModelTrustError):
    """Raised for input validation failures, file not found, or schema failures. Exit code 4."""
    pass

class NotAssessableError(ModelTrustError):
    """Raised when an audit or check cannot be performed (e.g. missing column)."""
    pass
