from .domain_error import DomainError


class ReglaDeNegocioViolada(DomainError):
    """Se rompió una invariante o regla de negocio del dominio."""
