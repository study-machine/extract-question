def uni_to_u8(s):
    if isinstance(s,unicode):
        return s.encode('utf8')
    return s
