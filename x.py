import yaml
import sys
import shutil
from fetchany.yamlreader import *


class AnnotatedStrA(str):
    def __new__(cls, text, start, end):
        o = str.__new__(cls, text)
        o._start = start
        o._end = end
        return o

    def __str__(self):
        return "{} ({}:{})".format(str.__str__(self), self._start, self._end)

    def __repr__(self):
        r = str.__repr__(self)
        return "MyStr({}, {}, {})".format(r, self._start, self._end)


class MyStr(str):
    def __new__(cls, text, extra):
        o = str.__new__(cls, text)
        o.extra = extra
        return o

    def __str__(self):
        return str.__str__(self)

    def __repr__(self):
        r = str.__repr__(self)
        return r



def create_annotated(l, n):
    s = l.construct_scalar(n)
    if isinstance(s, str):
        return MyStr(s, n)
    return s


#with open('example.yaml', 'r') as f:
#    s = yaml.SafeLoader(f)
#    s.add_constructor('tag:yaml.org,2002:str', create_annotated)
#    d = s.get_data()

shutil.copy('example.yaml', 'example.mod.yaml')
d = parse_annotated('example.mod.yaml')

f = open('example.mod.yaml', 'r+')
d['repos']['meta-raspberrypi']['protocol'].modify(f, 'httpx')
d['repos']['meta-openembedded']['protocol'].modify(f, 'ssh')
d['repos']['poky']['protocol'].modify(f, 'funny-nanny')
d['repos']['my-new-one'] = dict( url="git://myrepo.git"
                               , protocol='cool'
                               , revision="newest"
                               )
f.close()

with open('example.mod.yaml', 'w') as f:
    f.write(dump_yaml(d, default_flow_style=False))

d = parse_annotated('example.mod.yaml')

print("Modified\n--------")
print(dump_yaml(d, default_flow_style=False))
