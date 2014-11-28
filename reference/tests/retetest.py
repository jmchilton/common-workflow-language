import unittest
import cwltool.rete as rete
import cwltool.workflow as workflow

class ReteTest(unittest.TestCase):
    def test1(self):
        n = rete.Network()
        n.addrule([["a", "b", rete.Variable("?c")]],
                  [["e", "f", rete.Variable("?c")]],
                  [])

        n.propagate(None, ["a", "b", "q"])
        self.assertEqual(set([('a', 'b', 'q'), ('e', 'f', 'q')]), n.facts)

    def test2(self):
        n = rete.Network()
        n.addrule([["a", "b", rete.Variable("?c")], ["x", "y", rete.Variable("?c")]],
                  [["e", "f", rete.Variable("?c")]],
                  [])

        n.propagate(None, ["a", "b", "q"])
        self.assertEqual(set([('a', 'b', 'q')]), n.facts)

        n.propagate(None, ["x", "y", "q"])
        self.assertEqual(set([('a', 'b', 'q'), ('x', 'y', 'q'), ('e', 'f', 'q')]), n.facts)

    def test3(self):
        n = rete.Network()
        n.addrule([["a", "b", rete.Variable("?c")]],
                  [["e", "f", rete.Variable("?c")]],
                  [])
        n.addrule([["e", "f", rete.Variable("?g")]],
                  [["h", "i", rete.Variable("?g")]],
                  [])

        n.propagate(None, ["a", "b", "q"])
        self.assertEqual(set([('a', 'b', 'q'), ('e', 'f', 'q'), ('h', 'i', 'q')]), n.facts)

    def run_tool(self, step, network, row):
        network.propagate(None, [step, ":output", row[":file1"] + ".output"])

    def test4(self):
        w = workflow.Workflow()
        w.addStep(":first_step", [":file1"], self.run_tool)
        w.addStep(":second_step", [":file1"], self.run_tool)
        w.connectSteps(":first_step", ":output",
                       ":second_step", ":file1")

        w.network.propagate(None, [":first_step", ":file1", "hello.txt"])

        self.assertEqual(set([(':first_step', ':file1', 'hello.txt'),
                              (':first_step', ':output', 'hello.txt.output'),
                              (':second_step', ':file1', 'hello.txt.output'),
                              (':second_step', ':output', 'hello.txt.output.output')]), w.network.facts)

    def test5(self):
        w = workflow.Workflow()
        w.addStep(":first_step", [":file1"], self.run_tool)
        w.addStep(":second_step", [":file1"], self.run_tool)
        w.connectSteps(":first_step", ":output",
                       ":second_step", ":file1")

        w.network.propagate(None, [":first_step", ":file1", "hello.txt"])
        w.network.propagate(None, [":first_step", ":file1", "hello2.txt"])

        self.assertEqual(set([(':first_step',  ':file1',  'hello.txt'),
                              (':first_step',  ':output', 'hello.txt.output'),
                              (':second_step', ':file1',  'hello.txt.output'),
                              (':second_step', ':output', 'hello.txt.output.output'),
                              (':first_step',  ':file1',  'hello2.txt'),
                              (':first_step',  ':output', 'hello2.txt.output'),
                              (':second_step', ':file1',  'hello2.txt.output'),
                              (':second_step', ':output', 'hello2.txt.output.output')]), w.network.facts)

    def test6(self):
        w = workflow.Workflow()
        w.addStep(":first_step", [":file1"], self.run_tool)
        w.addStep(":second_step", [":file1"], self.run_tool)
        w.connectSteps(":first_step", ":output",
                                ":second_step", ":file1")
        w.connectSteps(":second_step", ":output",
                                ":first_step", ":file1",
                                lambda row: len(row["value"]) < 25)

        w.network.propagate(None, [":first_step", ":file1", "hello.txt"])

        self.assertEqual(set([(':first_step',  ':file1',  'hello.txt'),
                              (':first_step',  ':output', 'hello.txt.output'),
                              (':second_step', ':file1',  'hello.txt.output'),
                              (':second_step', ':output', 'hello.txt.output.output'),
                              (':first_step',  ':file1',  'hello.txt.output.output'),
                              (':first_step',  ':output', 'hello.txt.output.output.output'),
                              (':second_step', ':file1',  'hello.txt.output.output.output'),
                              (':second_step', ':output', 'hello.txt.output.output.output.output'),
                              ]), w.network.facts)
