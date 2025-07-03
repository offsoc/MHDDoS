import struct
import random
import os

def generate_payload(target, options=None):
    """
    ICMP Echo Request (ping) packet.
    options:
      - id: int, identifier (random if not set)
      - seq: int, sequence number (random if not set)
      - size: int, payload size (default 56)
      - mutate: bool, randomize content
    """
    ident = options.get('id', random.randint(0, 0xffff)) if options else random.randint(0, 0xffff)
    seq = options.get('seq', random.randint(0, 0xffff)) if options else random.randint(0, 0xffff)
    size = options.get('size', 56) if options else 56
    mutate = options.get('mutate', False) if options else False
    data = os.urandom(size) if mutate else b'A' * size
    header = struct.pack('!BBHHH', 8, 0, 0, ident, seq)
    # Calculate checksum
    def checksum(data):
        s = sum((data[i] << 8) + data[i+1] for i in range(0, len(data)-1, 2))
        if len(data) % 2:
            s += data[-1] << 8
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        return (~s) & 0xffff
    chksum = checksum(header + data)
    header = struct.pack('!BBHHH', 8, 0, chksum, ident, seq)
    return header + data
