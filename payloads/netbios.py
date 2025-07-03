import random

def generate_payload(target, options=None):
    """
    NetBIOS Name Service request, supports custom name/mutation
    options:
      - name: str, NetBIOS name
      - mutate: bool, whether to mutate
    """
    name = options.get('name', 'CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA') if options else 'CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    mutate = options.get('mutate', False) if options else False
    if mutate:
        name = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=32))
    return b'\x80\x00\x00\x10\x00\x01\x00\x00\x00\x00\x00\x00' + name.encode() + b'\x00\x00\x21\x00\x01'