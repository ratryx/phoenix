class JobCancelledError(Exception):
    """
    Exceção levantada quando uma operação em segundo plano é cancelada
    de forma cooperativa.
    """
    pass

class RootChangedError(Exception):
    """
    Exceção levantada quando a identidade (st_dev, st_ino) de uma raiz
    ou diretório muda durante a operação, indicando um possível ataque TOCTOU.
    """
    pass

class ProtectionError(Exception):
    """
    Exceção levantada quando uma operação de mutação destrutiva é chamada
    sem que o estado de proteção do sistema seja garantido (ponto de restauração
    criado ou risco explicitamente aceito).
    """
    pass
