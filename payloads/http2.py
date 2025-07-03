def generate_payload(target, options=None):
    # Example: forge HTTP2-like request
    path = options.get('path', '/') if options else '/'
    headers = [
        ':method: GET',
        f':path: {path}',
        ':scheme: https',
        f':authority: {target}',
        'user-agent: Mozilla/5.0 (compatible; CustomBot/1.0)'
    ]
    payload = '\r\n'.join(headers) + '\r\n\r\n'
    return payload.encode()