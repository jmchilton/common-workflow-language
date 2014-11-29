import rete
import rdflib
import tool
from ref_resolver import from_url
import json
import os

class RunStep(object):
    def __init__(self, prefix, basedir, tool):
        self.prefix = prefix
        self.basedir = basedir
        self.tool = tool

    def run(self, name, nw, row):
        job = {}
        job['inputs'] = {}
        for k, v in row.items():
            s = k[len(self.prefix):]
            job['inputs'][s] = json.loads(v)
        output = self.tool.job(job, self.basedir, use_container=False).run()
        for o in output:
            nw.propagate(None, (name, rdflib.URIRef(self.prefix+o), rdflib.Literal(json.dumps(output[o]), datatype="http://json.org")))

class Workflow(object):
    def __init__(self, wf=None, basedir=None):
        self.network = rete.Network()
        self.root = None
        self.inputs = []
        if wf:
            self.basedir = basedir if basedir else os.path.abspath(os.path.dirname(wf))
            self.load(wf)

    def addStep(self, name, input_ports, executor):
        self.network.addrule([(name, port, rete.Variable(port)) for port in input_ports],
                             [],
                             [lambda nw, row: executor(name, nw, row)])

    def connectSteps(self,
                     step1, output_port,
                     step2, input_port,
                     conditional=None):
        self.network.addrule([(step1, output_port, rete.Variable("value"))],
                             [(step2, input_port, rete.Variable("value"))],
                             [],
                             [conditional] if conditional else [])

    def load(self, wf):
        g = rdflib.Graph().parse(wf, format='json-ld')

        q = g.query('''
        prefix wf: <http://github.com/common-workflow-language/schema/wf#>
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        select ?step ?tool
        where {
                ?step rdf:type wf:step .
                ?step wf:tool ?tool .
                }
            ''')

        for r in q:
            t = tool.Tool(from_url(r[1]))
            self.addStep(r[0], [rdflib.URIRef(r[1]+"#"+a) for a in t.tool['inputs']['properties']],
                         RunStep(r[1]+"#", self.basedir, t).run)

        q = g.query('''
        prefix wf: <http://github.com/common-workflow-language/schema/wf#>
        select ?source ?source_port ?destination ?destination_port
        where {
                ?bn wf:source ?source .
                ?bn wf:source_port ?source_port .
                ?bn wf:destination ?destination .
                ?bn wf:destination_port ?destination_port .
                }
            ''')

        for r in q:
            self.connectSteps(r[0], r[1], r[2], r[3])

        q = g.query('''
        prefix wf: <http://github.com/common-workflow-language/schema/wf#>
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        select ?wf ?input
        where {
                ?wf rdf:type wf:Workflow .
                ?wf wf:inputs ?input .
                }
            ''')

        for r in q:
            self.root = r[0]
            self.inputs.append(r[1])

    def run(self, joborder):
        for k, v in joborder["inputs"].items():
            self.network.propagate(None, (self.root, rdflib.URIRef(self.root+"#"+k),
                    rdflib.Literal(json.dumps(v), datatype="http://json.org")))
