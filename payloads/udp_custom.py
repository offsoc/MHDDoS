def generate_payload(target, options=None):
    # Supports custom content and large packets
    content = options.get('content', 'A') if options else 'A'
    size = options.get('size', 65507) if options else 65507
    return (content * size).encode()[:size]