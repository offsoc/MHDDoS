import random

def generate_payload(target, options=None):
    """
    mDNS standard query, supports custom service name/mutation
    options:
      - service: str, service name
      - mutate: bool, whether to mutate
    """
    service = options.get('service', '_services._dns-sd._udp.local') if options else '_services._dns-sd._udp.local'
    mutate = options.get('mutate', False) if options else False
    if mutate:
        service = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(5,15))) + '._udp.local'
    q = b'\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00'
    for part in service.split('.'):
        q += bytes([len(part)]) + part.encode()
    q += b'\x00\x0c\x00\x01'
    return q