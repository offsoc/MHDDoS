def generate_payload(target, options=None):
    """
    Supports custom content and large packets, optimized for minimal hardware usage.
    options:
      - content: str, content
      - size: int, packet size (default 65507)
      - static: bool, if True, reuse static buffer (default False)
    """
    content = options.get('content', 'A') if options else 'A'
    size = options.get('size', 65507) if options else 65507
    static = options.get('static', False) if options else False
    if static:
        # Use a static buffer for repeated content
        if not hasattr(generate_payload, "_static_buf") or len(generate_payload._static_buf) < size:
            generate_payload._static_buf = bytearray((content * size).encode()[:size])
        return memoryview(generate_payload._static_buf)[:size]
    return (content * size).encode()[:size]