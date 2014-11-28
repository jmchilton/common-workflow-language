import rdflib
from rdflib import URIRef, BNode, Literal
import cwltool.rete as rete
import cwltool.workflow
import unittest
import logging

class WfTest(unittest.TestCase):
    def test1(self):
        #rete.logger.setLevel(logging.DEBUG)

        wf = cwltool.workflow.Workflow("../examples/sort-rev-workflow.jsonld")
        #print wf.root
        #print wf.inputs
        wf.network.propagate(None, (wf.root, wf.inputs[0],
                                    Literal('{"path":"sortme.txt"}', datatype="http://json.org")))

        rete.logger.setLevel(logging.INFO)
