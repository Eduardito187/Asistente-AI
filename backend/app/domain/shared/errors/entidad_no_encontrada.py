from .domain_error import DomainError


class EntidadNoEncontrada(DomainError):
    """El agregado solicitado no existe."""
