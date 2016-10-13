#!/usr/bin/python

import gv
import sys
import xml.etree.ElementTree as XMLTree


########################################################################
########################################################################


class GraphVizObject(object):

    def __init__(self):
        self.__handle = None

    def handle(self):
        return self.__handle

    def set_handle(self, handle):
        self.__handle = handle


class Process(GraphVizObject):
    """A process takes a set of products as inputs and produces a set of
    products as outputs.  Optionally, the process can have a technology
    requirement.
    """

    __processes = {}

    @classmethod
    def by_name(cls, name, create_if_needed=False):
        obj = cls.__products.get(name, None)
        if obj is None and create_if_needed:
            obj = cls(name)
        if obj is None:
            raise NameError, "No such {1} {0!r}".format(name, cls.__name__)
        if not isinstance(obj, cls):
            raise TypeError, "Type mismatch: {0!r} is {1} not {2}".format(name, cls.__name__, obj.__class__.__name__)
        return obj

    @classmethod
    def get_all(cls):
        return set(cls.__processes.itervalues())

    def __init__(self, name, inputs = (), outputs = (), technology = None):
        if len(inputs) == 0 and len(outputs) == 0:
            raise ValueError, "A Process must have at least one input or one output."
        self.__name = name
        self.__inputs = tuple(inputs)
        self.__outputs = tuple(outputs)
        self.__technology = technology
        self.__processes[name] = self

    def name(self):
        return self.__name

    def technology(self):
        return self.__technology

    def inputs(self):
        return tuple(self.__inputs)

    def outputs(self):
        return tuple(self.__outputs)

    def add_to_graph(self, graph):
        node = gv.node(graph, self.__name)
        self.set_handle(node)
        gv.setv(node, 'shape', 'none')
        # +----------------+
        # |  process name  |
        # +----+-----+-----+
        # | in |     |     |
        # +----+ --> | out |
        # | in |     |     |
        # +----+-----+-----+
        # |   technology   |
        # +----------------+
        title = '<tr><td colspan="3">{0}</td></tr><hr/>'.format(self.__name)
        inputs = '<table border="0">{0}</table>'.format('<hr/>'.join(['<tr><td port="{0}"><font color="{1}">{0}</font></td></tr>'.format(input.name(), input.color()) for input in self.__inputs]))
        if len(self.__outputs) > 0:
            outputs = '<table border="0">{0}</table>'.format('<hr/>'.join(['<tr><td port="{0}"><font color="{1}">{0}</font></td></tr>'.format(output.name(), output.color()) for output in self.__outputs]))
        else:
            outputs = ''
        process = '<tr><td>{0}</td><vr/><td> &rarr; </td><vr/><td>{1}</td></tr>'.format(inputs, outputs)
        if self.__technology is None:
            technology = ''
        else:
            technology = '<hr/><tr><td colspan="3">{0}</td></tr>'.format(self.__technology)
        html = '<table border="1" cellborder="0">{0}{1}{2}</table>'.format(title, process, technology)
        #print >> sys.stderr, "process {0!r} label {1!r}".format(self, html)
        gv.setv(node, 'label', '<{0}>'.format(html))

    def __repr__(self):
        #print >> sys.stderr, "In repr for {0}({1!r})".format(self.__class__.__name__, self.__name)
        return "{0}(name={1!r}, inputs={2!r}, outputs={3!r}, technology={4!r})".format(self.__class__.__name__, self.__name, [x.name() for x in self.__inputs], [x.name() for x in self.__outputs], self.__technology)

class BaseResource(GraphVizObject):
    """A product that can be produced or consumed by a process.

    BaseResource is an abstract class that cannot be directly instantiated.
    It is only used as the parent class for the Resource and ResourceAlias
    classes.
    """

    __products = {}

    @classmethod
    def by_name(cls, name, create_if_needed=False):
        obj = cls.__products.get(name, None)
        if obj is None and create_if_needed:
            obj = cls(name)
        if obj is None:
            raise NameError, "No such {1} {0!r}".format(name, cls.__name__)
        if not isinstance(obj, cls):
            raise TypeError, "Type mismatch: {0!r} is {1} not {2}".format(name, cls.__name__, obj.__class__.__name__)
        return obj

    @classmethod
    def get_all(cls):
        return set([obj for obj in cls.__products.itervalues() if isinstance(obj, cls)])

    def __init__(self, name):
        if self.__class__ == BaseResource:
            raise ValueError, "BaseResource cannot be directly instantiated."
        if name in self.__products:
            raise ValueError, "Not allowed to redefine {1}({0!r}) as {2}({0!r}).".format(name, self.__products[name].__class__.__name__, self.__class__.__name__)
        self.__name = name
        self.__type = None
        self.__products[name] = self

    def name(self):
        return self.__name

    def type(self):
        return self.__type

    def set_type(self, typ):
        self.__type = typ

    def color(self):
        if self.__type == 'liquid':
            return '#0000ff'
        elif self.__type == 'gas':
            return '#ff0080'
        else:
            return '#000000'

    def __repr__(self):
        #print >> sys.stderr, "In repr for {0}({1!r})".format(self.__class__.__name__, self.__name)
        return "{0}({1!r})".format(self.__class__.__name__, self.__name)

    def __str__(self):
        return self.__name


class Resource(BaseResource):
    """A real product that is produced and/or consumed by processes."""

    def __init__(self, name):
        super(Resource,self).__init__(name)
        self.__produced_by = set()
        self.__consumed_by = set()
        self.__aka = set()

    def produced_by(self):
        return set(self.__produced_by)

    def add_producer(self, producer):
        self.__produced_by.add(producer)

    def consumed_by(self):
        return set(self.__consumed_by)

    def add_consumer(self, consumer):
        self.__consumed_by.add(consumer)

    def aka(self):
        return set(self.__aka)

    def add_aka(self, aka):
        self.__aka.add(aka)

    def add_to_graph(self, graph):
        if len(self.__produced_by) == 0:
            node = gv.node(graph, self.name())
            self.set_handle(node)
            gv.setv(node, 'shape', 'ellipse')
            gv.setv(node, 'label', '<<table border="0"><tr><td port="{0}"><font color="{1}">{0}</font></td></tr></table>>'.format(self.name(), self.color()))
        # add connections
        if len(self.__produced_by) == 0:
            producers = [self]
        else:
            producers = self.__produced_by
        for producer in producers:
            for consumer in self.__consumed_by:
                edge = gv.edge(producer.handle(), consumer.handle())
                gv.setv(edge, 'headport', '{0}:w'.format(self.name()))
                gv.setv(edge, 'tailport', '{0}:e'.format(self.name()))
                gv.setv(edge, 'color', self.color())

    def __repr__(self):
        r = super(Resource,self).__repr__()
        if len(self.__produced_by) > 0:
            r += ' produced by {0!r}'.format(tuple(sorted([x.name() for x in self.__produced_by])))
        if len(self.__consumed_by) > 0:
            r += ' consumed by {0!r}'.format(tuple(sorted([x.name() for x in self.__consumed_by])))
        if len(self.__aka) > 0:
            r += ' aka {0!r}'.format(tuple(sorted([x.name() for x in self.__aka])))
        return r


class ResourceAlias(Resource):
    """An alias that represents one or more real products."""

    def __init__(self, name):
        super(ResourceAlias,self).__init__(name)
        self.__alias_for = set()

    def alias_for(self):
        return set(self.__alias_for)

    def add_alias(self, alias):
        self.__alias_for.add(alias)

    def add_to_graph(self, graph):
        for alias in self.__alias_for:
            producers = alias.produced_by()
            if len(producers) == 0:
                producers = [alias]
            for producer in producers:
                for consumer in self.consumed_by():
                    edge = gv.edge(producer.handle(), consumer.handle())
                    gv.setv(edge, 'headport', '{0}:w'.format(self.name()))
                    gv.setv(edge, 'tailport', '{0}:e'.format(alias.name()))

    def __repr__(self):
        r = super(ResourceAlias,self).__repr__()
        if len(self.__alias_for) > 0:
            r += ' alias for {0!r}'.format(tuple(sorted([x.name() for x in self.__alias_for])))
        return r

########################################################################
########################################################################

# Parse the production.xml XML tree into Process, Resource, and
# ResourceAlias objects.


xmlfile = XMLTree.parse('production.xml')
production = xmlfile.getroot()

for resource in production.findall('resource'):
    res = Resource(resource.get('name'))
    res.set_type(resource.get('type', 'solid'))
    for alias in resource.findall('alias'):
        a = ResourceAlias.by_name(alias.get('name'), create_if_needed=True)
        a.add_alias(res)
        res.add_aka(a)

# first step: create, if needed, all the 'produced' products
for process in production.findall('process'):
    for produced in process.findall('produces'):
        Resource.by_name(produced.get('name'), create_if_needed=True)

# second step: create the processes and set up all the inputs/outputs/produced_by/consumed_by lists
for process in production.findall('process'):
    inputs = [BaseResource.by_name(consumed.get('name')) for consumed in process.findall('consumes')]
    outputs = [Resource.by_name(produced.get('name')) for produced in process.findall('produces')]
    technology = process.findall('technology')
    technology = technology[0].get('name') if len(technology) > 0 else None
    process = Process(process.get('name'), inputs, outputs, technology)
    for input in inputs:
        input.add_consumer(process)
    for output in outputs:
        output.add_producer(process)


########################################################################
########################################################################

# Create the graph


graph = gv.digraph('production')
gv.setv(graph, 'rankdir', 'LR')

defnode = gv.protonode(graph)
gv.setv(defnode, 'shape', 'record')

resources = gv.graph(graph, 'resources')
gv.setv(resources, 'rank', 'source')

processes = gv.graph(graph, 'processes')

goals = gv.graph(graph, 'goals')
gv.setv(goals, 'rank', 'sink')

# add each process into either the processes or goals subgraph, depending
# on whether or not it has any outputs

for process in Process.get_all():
    if len(process.outputs()) == 0:
        process.add_to_graph(goals)
    else:
        process.add_to_graph(processes)

# add each resource into the resources subgraph
# and each other product into the processes subgraph.
# a product is a resource if it has no producers.

for resource in Resource.get_all():
    if len(resource.produced_by()) == 0:
        consumed = len(resource.consumed_by()) > 0
        if not consumed:
            for aka in resource.aka():
                if len(aka.consumed_by()) > 0:
                    consumed = True
        if consumed:
            resource.add_to_graph(resources)
    else:
        resource.add_to_graph(processes)

gv.write(graph, 'production.dot')

gv.layout(graph, 'dot')
gv.render(graph, 'png', 'production.png')
