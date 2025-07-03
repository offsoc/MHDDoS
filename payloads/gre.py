import os

def generate_payload(target, options=None):
    """
    GRE (Generic Routing Encapsulation) packet.
    options:
      - size: int, payload size (default 1400)
      - mutate: bool, randomize content
    """
    size = options.get('size', 1400) if options else 1400
    mutate = options.get('mutate', False) if options else False
    gre_header = b'\x00\x00\x08\x00'
    payload = os.urandom(size) if mutate else b'A' * size
    return gre_header + payload
