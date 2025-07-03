import os
# Pre-allocate a static buffer for maximum efficiency
_STATIC_UDP_PB_PAYLOAD = bytearray(b'A' * 65507)

def generate_payload(target, options=None):
    """
    PB-level traffic forging, maximum packet, optimized for minimal hardware usage.
    options:
      - size: int, packet size (default 65507)
      - randomize: bool, if True, randomize content (default False)
    """
    size = options.get('size', 65507) if options else 65507
    randomize = options.get('randomize', False) if options else False
    if not randomize:
        return memoryview(_STATIC_UDP_PB_PAYLOAD)[:size]
    else:
        import random
        return bytes(random.getrandbits(8) for _ in range(size))