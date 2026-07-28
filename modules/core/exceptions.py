class JobCancelledError(Exception):
    """
    Exceção levantada quando uma operação em segundo plano é cancelada
    de forma cooperativa.
    """
    pass
