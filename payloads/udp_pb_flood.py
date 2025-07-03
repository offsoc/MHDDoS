import os
def generate_payload(target, options=None):
    # PB-level traffic forging, maximum packet
    size = options.get('size', 65507) if options else 65507
    return b'A' * size