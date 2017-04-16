import yaml
import logging
import collections
from neobunch import NeoBunch



def walk_collection(obj, func, top=None, **kwargs):
    if top is None:
        top = obj
    logging.debug("walk: current={}, kwargs={}".format(obj, kwargs))
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
    def __new__(cls, text, node):
        o = str.__new__(cls, text)
        o.__value = node.value
        o.__top = None
        o.__start = node.start_mark.index
        o.__end = node.end_mark.index
        o.__next_start = o.__end
        if node.style in ('"', "'"):
            if (len(node.value) + 2) != (o.__end - o.__start):
                raise ValueError("Unexpected length: node={},style={}".format(node, node.style))
            o.__start += 1
            o.__end -= 1
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
        return str.__str__(self)

    def __repr__(self):
        return str.__repr__(self)


def _create_annotated_str(loader, node):
    obj = loader.construct_scalar(node)
    if isinstance(obj, str):
        return AnnotatedStr(obj, node)
    return obj


def _insert_ref(obj, top=None):
    if isinstance(obj, AnnotatedStr):
        obj._add_top_ref(top)


def parse_annotated(path):
    nb = NeoBunch()
    nb['path'] = path
    with open(path, 'r') as f:
        loader = yaml.SafeLoader(f)
        loader.add_constructor('tag:yaml.org,2002:str', _create_annotated_str)
        # TODO: Wrap the top level element to reload on modification (to fix
        #       start / end marker positions)
        nb.update(loader.get_data())
        walk_collection(nb, _insert_ref)
        return nb
