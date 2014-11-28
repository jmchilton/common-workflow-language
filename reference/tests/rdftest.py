import rdflib
from rdflib import URIRef, BNode, Literal
import cwltool.rete as rete
import unittest

class ReteRdfTest(unittest.TestCase):
    def test1(self):
        e = rdflib.Namespace("http://example.com/")
        n = rete.Network()
        n.addrule([[e.a, e.b, rete.Variable("?c")]],
                  [[e.e, e.f, rete.Variable("?c")]],
                  [])

        n.propagate(None, [e.a, e.b, Literal("q")])
        self.assertEqual(set([(e.a, e.b, Literal('q')), (e.e, e.f, Literal('q'))]), n.facts)

    def test2(self):
        e = rdflib.Namespace("http://example.com/")
        n = rete.Network()
        n.addrule([[e.a, e.b, rete.Variable("?c")]],
                   [[e.e, e.f, rete.Variable("?c")]],
                  [])

        testdata = '''
        {
        "@context": { "@base": "http://example.com/", "b": "http://example.com/b" },
        "@id": "a",
        "b": "q"
        }'''

        g = rdflib.Graph().parse(data=testdata, format='json-ld')

        for r in g:
            n.propagate(None, r)

        self.assertEqual(set([(e.a, e.b, Literal('q')), (e.e, e.f, Literal('q'))]), n.facts)
