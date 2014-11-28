import logging
# simple assertion-only rete network.

logger = logging.getLogger('cwltool.rete')
logger.addHandler(logging.StreamHandler())

class Variable(object):
    def __init__(self, name):
        self.name = name

class Node(object):
    def __init__(self):
        self.children = []

    def addchild(self, b):
        if b not in self.children:
            self.children.append(b)
            b.addparent(self)

    def addparent(self, p):
        pass

class Alpha(Node):
    def __init__(self, triple):
        super(Alpha, self).__init__()
        self.triple = triple

    def propagate(self, parent, fact):
        row = {}

        # bind variables and check equality for ground values
        for i in xrange(0, 3):
            if isinstance(self.triple[i], Variable):
                row[self.triple[i].name] = fact[i]
            elif self.triple[i] != fact[i]:
                return

        logger.debug("matched %s" % str(fact))

        for c in self.children:
            c.propagate(self, row)


class Beta(Node):
    def __init__(self):
        super(Beta, self).__init__()
        self.wm = []
        self.parents = []

    def addparent(self, p):
        if p not in self.parents:
            if len(self.parents) > 1:
                raise Exception("maximum two parents for beta node")
            self.parents.append(p)
            self.wm.append([])

    def propagate(self, parent, row):
        for i, p in enumerate(self.parents):
            if p == parent:
                side = i

        # discard if we have seen this already
        for m in self.wm[side]:
            if m == row:
                return

        # save the row
        self.wm[side].append(row)

        otherside = self.wm[int(not side)]

        # try to join
        for o in otherside:
            logger.debug("try join %s and %s" % (str(o), str(row)))

            propagate = True
            for var in row:
                if var in o and row[var] != o[var]:
                    propagate = False
                    break

            if propagate:
                p = o.copy()
                p.update(row)

                for c in self.children:
                    c.propagate(self, p)

class Conditional(Node):
    def __init__(self, condition):
        super(Conditional, self).__init__()
        self.condition = condition

    def propagate(self, parent, row):
        if self.condition(row):
            for c in self.children:
                c.propagate(self, row)

class Production(Node):
    def __init__(self, triple):
        super(Production, self).__init__()
        self.triple = triple

    def propagate(self, parent, row):
        l = []
        for i in xrange(0, 3):
            if isinstance(self.triple[i], Variable):
                l.append(row[self.triple[i].name])
            else:
                l.append(self.triple[i])

        logger.debug("producing %s" % str(l))

        for c in self.children:
            c.propagate(self, l)

class Action(Node):
    def __init__(self, network, action):
        super(Action, self).__init__()
        self.action = action
        self.network = network

    def propagate(self, parent, row):
        self.action(self.network, row)

class Network(Node):
    def __init__(self):
        super(Network, self).__init__()
        self.facts = set()

    def addrule(self, match, production, action=[], conditional=[]):
        lastnode = None
        for m in match:
            logger.debug("creating alpha for %s" % str(m))
            alpha = Alpha(m)
            self.addchild(alpha)
            if lastnode:
                beta = Beta()
                alpha.addchild(beta)
                lastnode.addchild(beta)
                lastnode = beta
            else:
                lastnode = alpha

        for c in conditional:
            cond = Conditional(c)
            lastnode.addchild(cond)
            lastnode = cond

        for p in production:
            pr = Production(p)
            lastnode.addchild(pr)
            pr.addchild(self)

        for a in action:
            lastnode.addchild(Action(self, a))

    def propagate(self, parent, fact):
        t = tuple(fact)
        if t in fact:
            return
        self.facts.add(t)
        for a in self.children:
            a.propagate(self, fact)
