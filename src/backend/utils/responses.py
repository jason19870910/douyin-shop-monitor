"""Unified API response helpers for consistent error/success formatting."""
from typing import Any, Optional, TypeVar
from flask import jsonify, Response

T = TypeVar('T')


class ApiResponse:
    """Standardized API response structure.
    
    All endpoints should return responses using these helpers to ensure
    consistent format across the API.
    """
    
    @staticmethod
    def success(data: Any = None, message: str = None, code: int = 200) -> Response:
        """Create a successful response.
        
        Args:
            data: Response payload (can be any JSON-serializable type)
            message: Optional success message
            code: HTTP status code (default 200)
            
        Returns:
            Flask Response with standardized JSON structure
        """
        response = {
            'success': True,
            'data': data,
            'error': None
        }
        if message:
            response['message'] = message
        return jsonify(response), code

    @staticmethod
    def error(message: str, code: int = 400, error_code: str = None, details: Any = None) -> Response:
        """Create an error response.
        
        Args:
            message: Human-readable error message
            code: HTTP status code (default 400)
            error_code: Optional machine-readable error code
            details: Optional additional error details
            
        Returns:
            Flask Response with standardized JSON structure
        """
        response = {
            'success': False,
            'data': None,
            'error': message
        }
        if error_code:
            response['error_code'] = error_code
        if details is not None:
            response['details'] = details
        return jsonify(response), code

    @staticmethod
    def not_found(resource: str = 'Resource', code: int = 404) -> Response:
        """Create a 404 not found response."""
        return ApiResponse.error(f'{resource} not found', code=code, error_code='NOT_FOUND')

    @staticmethod
    def bad_request(message: str = 'Invalid request', details: Any = None) -> Response:
        """Create a 400 bad request response."""
        return ApiResponse.error(message, code=400, error_code='BAD_REQUEST', details=details)

    @staticmethod
    def unauthorized(message: str = 'Unauthorized') -> Response:
        """Create a 401 unauthorized response."""
        return ApiResponse.error(message, code=401, error_code='UNAUTHORIZED')

    @staticmethod
    def forbidden(message: str = 'Forbidden') -> Response:
        """Create a 403 forbidden response."""
        return ApiResponse.error(message, code=403, error_code='FORBIDDEN')

    @staticmethod
    def internal_error(message: str = 'Internal server error', details: Any = None) -> Response:
        """Create a 500 internal server error response."""
        return ApiResponse.error(message, code=500, error_code='INTERNAL_ERROR', details=details)

    @staticmethod
    def validation_error(message: str, details: Any = None) -> Response:
        """Create a 422 validation error response."""
        return ApiResponse.error(message, code=422, error_code='VALIDATION_ERROR', details=details)


# Convenience functions for common patterns
def success_response(data: Any = None, message: str = None, code: int = 200) -> Response:
    """Convenience function for successful responses."""
    return ApiResponse.success(data, message, code)


def error_response(message: str, code: int = 400, error_code: str = None, details: Any = None) -> Response:
    """Convenience function for error responses."""
    return ApiResponse.error(message, code, error_code, details)


def not_found_response(resource: str = 'Resource') -> Response:
    """Convenience function for 404 responses."""
    return ApiResponse.not_found(resource)


def bad_request_response(message: str = 'Invalid request', details: Any = None) -> Response:
    """Convenience function for 400 responses."""
    return ApiResponse.bad_request(message, details)


def unauthorized_response(message: str = 'Unauthorized') -> Response:
    """Convenience function for 401 responses."""
    return ApiResponse.unauthorized(message)


def internal_error_response(message: str = 'Internal server error', details: Any = None) -> Response:
    """Convenience function for 500 responses."""
    return ApiResponse.internal_error(message, details)