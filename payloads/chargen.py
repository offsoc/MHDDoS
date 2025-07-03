import random

def generate_payload(target, options=None):
    """
    Chargen protocol, supports custom content/mutation
    options:
      - content: str, content
      - mutate: bool, whether to mutate
    """
    content = options.get('content', '') if options else ''
    mutate = options.get('mutate', False) if options else False
    if mutate or not content:
        content = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=512))
    return content.encode()[:512]