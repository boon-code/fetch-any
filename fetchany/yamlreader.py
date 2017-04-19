import logging
import copy
import collections
try:
    from ruamel import yaml
    from ruamel.yaml.scalarstring import SingleQuotedScalarString, DoubleQuotedScalarString
    _use_ruamel = True
except ImportError:
    logging.debug("Fallback to normal yaml")
    import yaml
    _use_ruamel = False
    SingleQuotedScalarString = str
    DoubleQuotedScalarString = str

from neobunch import NeoBunch, neobunchify, unneobunchify



def walk_collection(obj, func, top=None, **kwargs):
    if top is None:
        top = obj
#    logging.debug("walk: current={}, kwargs={}".format(obj, kwargs))
    func(obj, top, **kwargs)
    if isinstance(obj, dict):
        for k,v in obj.items():
            walk_collection(k, func, top=top, **kwargs)
            walk_collection(v, func, top=top, **kwargs)
    if isinstance(obj, list):
        for v in obj:
            walk_collection(v, func, top=top, **kwargs)


def resolve_annotation(obj, top, offset=0, start=-1):
    if isinstance(obj, AnnotatedStr) and (offset != 0):
        obj._resolve_position(start, offset)


class ModifiedError(Exception):
    def __init__(self, oval, nval, start, end):
        t = "Node has been modified: expected='{}', actual='{}' ({}:{})".format\
                (oval, nval, start, end)
        Exception.__init__(self, t)
        self.oval = oval
        self.nval = nval
        self.start = start
        self.end = end


class AnnotatedStr(str):
    yaml_tag = u'tag:yaml.org,2002:str'

    @classmethod
    def construct(cls, loader, node):
        logging.debug("Construct {0}".format(node))
        logging.debug("Loader: {0} (type: {1})".format(loader, type(loader)))
        logging.debug("Preserve: {0}".format(loader._preserve_quotes))
        logging.debug("Style: {0}".format(node.style))
        logging.debug("Value: {0}".format(node.value))
        s = node.start_mark.index
        e = node.end_mark.index
        l = e-s
        logging.debug(" start: {0}, end: {1}, (len: {2})".format(s, e, l))
#        if node.style == '"':
            # TODO: Continue
#            obj = loader.construct_
        obj = loader.construct_scalar(node)
        logging.debug("obj: {0} (type: {1})".format(obj, type(obj)))
        if isinstance(obj, str):
            return cls(obj, node)
        else:
            logging.error("Unexpected")
            return obj

    @classmethod
    def to_yaml(cls, dumper, data):
        return data.__quote_func(dumper, data)

    def __new__(cls, text, node):
        o = super(AnnotatedStr, cls).__new__(cls, text)
        o.__value = node.value
        o.__top = None
        o.__start = node.start_mark.index
        o.__end = node.end_mark.index
        o.__quote_func = lambda d,v: d.represent_str(str(v))
        logging.debug("Class type for {0}: {1}".format(o.__value, type(node)))
        if node.style in ('"', "'"):
            if (len(node.value) + 2) != (o.__end - o.__start):
                raise ValueError("Unexpected length: node={},style={}".format(node, node.style))
            o.__start += 1
            o.__end -= 1
            if node.style == '"':
                quote_cls = DoubleQuotedScalarString
            else:
                quote_cls = SingleQuotedScalarString
            o.__quote_func = lambda d,v: d.represent_preserved_scalarstring(quote_cls(str(v)))
        return o

    def _add_top_ref(self, top):
        self.__top = top

    def _resolve_position(self, start, offset):
        if (self.__start >= start) and (start >= 0):
            self.__start += offset
            self.__end += offset

    def modify(self, fobj, value):
        s = self.__start
        e = self.__end
        l = e - s
        if l < 0:
            raise ValueError("Node[{}:{}] is illegal".format(s, e))
        ov = self.__value
        fobj.seek(s, 0)
        tmp = fobj.read(l)
        if ov != tmp:
            raise ModifiedError(ov, tmp, s, e)
        if ov == value:
            return
        offset = len(value) - len(ov)
        fobj.seek(s, 0)
        if offset == 0:
            fobj.write(value)
            fobj.flush()
        else:
            fobj.seek(e, 0)
            d = fobj.read()
            fobj.seek(s, 0)
            fobj.write(value)
            fobj.write(d)
            fobj.truncate()
            fobj.flush()
            walk_collection( self.__top
                           , resolve_annotation
                           , start = e
                           , offset=offset
                           )
        fobj.seek(0, 0)

    def __str__(self):
        return super(AnnotatedStr, self).__str__()

    def __repr__(self):
        return super(AnnotatedStr, self).__repr__()


#def _create_annotated_str(loader, node):
#    obj = loader.construct_scalar(node)
#    if isinstance(obj, str):
#        return AnnotatedStr(obj, node)
#    return obj


def _insert_ref(obj, top=None):
    if isinstance(obj, AnnotatedStr):
        obj._add_top_ref(top)


def dump_yaml(obj, **kwargs):
    try:
        repr_class = yaml.RoundTripRepresenter
        dumper = yaml.RoundTripDumper
    except AttributeError:
        logging.debug("Fallback to SafeRepresenter")
        repr_class = yaml.SafeDumper
        dumper = yaml.SafeDumper
    repr_class.add_representer(AnnotatedStr, AnnotatedStr.to_yaml)
    return yaml.dump(obj, Dumper=dumper, **kwargs)


def parse_annotated(path):
    with open(path, 'r') as f:
        try:
            loader = yaml.RoundTripLoader(f, preserve_quotes=True)
        except AttributeError:
            logging.debug("Fall back to SafeLoader")
            loader = yaml.SafeLoader(f)
        loader.add_constructor(AnnotatedStr.yaml_tag, AnnotatedStr.construct)
        cfg = loader.get_data()
        walk_collection(cfg, _insert_ref)
        return cfg
