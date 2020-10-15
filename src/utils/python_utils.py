def str2bool(str: str):
    if str.lower() in ['yes', 'true', 't', 'y', '1']:
        return True
    elif str.lower() in ['no', 'false', 'n', 'f', '0']:
        return False
    else:
        raise AttributeError('%s cannot be regarded as bool' % str)

