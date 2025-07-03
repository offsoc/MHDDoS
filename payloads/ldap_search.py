import random


def generate_payload(target, options=None):
    """
    LDAP search request (simple).
    options:
      - base_dn: str
      - filter: str
      - mutate: bool
    """
    base_dn = options.get('base_dn', '') if options else ''
    filter_str = options.get('filter', '(objectClass=*)') if options else '(objectClass=*)'
    mutate = options.get('mutate', False) if options else False
    if mutate:
        base_dn = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(3, 8)))
        filter_str = f"(uid={random.randint(1000, 9999)})"
    # Minimal LDAP search request (ASN.1 BER encoding, not a full implementation)
    # For simulation only
    return (
        b'\x30\x1d\x02\x01\x01\x63\x18\x04\x00\x0a\x01\x00\x0a\x01\x00\x02\x01\x00\x02\x01\x00'
        b'\x01\x01\x00\xa0\x0b\xa3\x09\x04\x00\x04\x00\x02\x01\x00\x87\x00'
    )
