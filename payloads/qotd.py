import random

def generate_payload(target, options=None):
    """
    QOTD protocol, supports custom content/mutation
    options:
      - content: str, content
      - mutate: bool, whether to mutate
    """
    content = options.get('content', '') if options else ''
    mutate = options.get('mutate', False) if options else False
    if mutate:
        content = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=random.randint(1,32)))
    return content.encode()[:512] if content else b'\x00'