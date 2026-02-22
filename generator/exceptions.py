"""Custom exceptions for api-test-data-generator."""


class SchemaLoadError(Exception):
    """Raised when a schema file cannot be loaded or parsed."""


class UnsupportedFieldTypeError(Exception):
    """Raised when a schema field type has no registered handler."""


class ValidationError(Exception):
    """Raised when generated data fails JSON Schema validation."""


class ExportError(Exception):
    """Raised when data cannot be exported to the desired format."""
