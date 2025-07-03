def generate_payload(target, options=None):
    """
    RDP (Remote Desktop Protocol) amplification request.
    options:
      - static: bool, use static buffer
    """
    # Standard RDP Connection Request (minimal)
    base = b'\x03\x00\x00\x13\x0e\xe0\x00\x00\x00\x00\x00\x01\x00\x08\x00\x03\x00\x00\x00\x00'
    if options and options.get('static'):
        if not hasattr(generate_payload, "_static_buf"):
            generate_payload._static_buf = base
        return generate_payload._static_buf
    return base
