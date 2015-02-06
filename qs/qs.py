
import re
from urlparse import unquote
from urllib import quote_plus


def merge(source, destination):
    """
    taken from: http://stackoverflow.com/a/20666342

    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            if (isinstance(value, list) or isinstance(value, tuple))\
                and key in destination:
                value = destination[key] + value
            destination[key] = value

    return destination


def qs_parse(qs, keep_blank_values=False, strict_parsing=False):
    tokens = {}
    pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]

    def get_name_value(name, value):
        name = unquote(name.replace('+', ' '))
        value = unquote(value.replace('+', ' '))
        matches = re.findall(r'([\s\w]+|\[\]|\[\w+\])', name)

        for i, match in enumerate(matches[::-1]):
            if match == '[]':
                if i == 0:
                    value = [value]
                else:
                    value += value
            elif re.match(r'\[\w+\]', match):
                name = re.sub(r'[\[\]]', '', match)
                value = {name: value}
            else:
                is_list = isinstance(value, list) or isinstance(value, tuple)
                is_dict = isinstance(value, dict)

                if is_list:
                    match = match + '[]'

                if match not in tokens:
                    tokens[match] = [] if not is_dict else {}

                if i == 0:
                    tokens[match] = [value]
                elif is_dict:
                    tokens[match] = merge(value, tokens[match])
                elif is_list:
                    tokens[match] = tokens[match] + list(value)
                else:
                    tokens[match].append(value)

    for name_val in pairs:
        if not name_val and not strict_parsing:
            continue
        nv = name_val.split('=')

        if len(nv) != 2:
            if strict_parsing:
                raise ValueError("bad query field: %r" % (name_value,))
            # Handle case of a control-name with no equal sign
            if keep_blank_values:
                nv.append('')
            else:
                continue

        if len(nv[1]) or keep_blank_values:
            get_name_value(nv[0], nv[1])

    return tokens


def build_qs(query):

    def dict_generator(indict, pre=None):
        pre = pre[:] if pre else []
        if isinstance(indict, dict):
            for key, value in indict.items():
                if isinstance(value, dict):
                    for d in dict_generator(value, pre + [key]):
                        yield d
                else:
                    yield pre + [key, value]
        else:
            yield indict

    paths = [i for i in dict_generator(query)]
    qs = []

    for path in paths:
        names = path[:-1]
        value = path[-1]
        s = []
        for i, n in enumerate(names):
            n = '[%s]' % n if i > 0 else n
            s.append(n)

        if isinstance(value, list) or isinstance(value, tuple):
            for v in value:
                multi = s[:]
                if not s[-1].endswith('[]'):
                    multi.append('[]')
                multi.append('=')
                multi.append(v)
                qs.append(''.join(multi))
        else:
            s.append('=')
            s.append(str(value))
            qs.append(''.join(s))

    return '&'.join(qs)
