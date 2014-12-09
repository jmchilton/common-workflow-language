#!/usr/bin/env python

import json
import argparse
import sys
import jsonschema
import cwltool.tool as tool
import os
import copy

from cwltool.ref_resolver import from_url

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tool", type=str)
    args = parser.parse_args()

    try:
        t = tool.Tool(from_url(args.tool))
    except jsonschema.exceptions.ValidationError as e:
        print "Tool definition failed validation"
        print e
        return 1

    if 'outputs' not in t.tool:
        print "Must have an outputs section"
        return 1

    w = sys.stdout

    w.write("<?xml version=\"1.0\"?>\n")
    w.write("<tool id=\"%s\" name=\"%s\">\n" % (os.path.basename(args.tool), os.path.basename(args.tool)))

    w.write("  <inputs>\n")

    def handle_param(k, v, indent):
        #print v
        if v['type'] == 'array':
            w.write(indent+"<repeat name=\"%s\">\n" % k)
            if 'type' in v['items']:
                if v['items']['type'] == 'object' and not ('_type' in v['items'] and v['items']['_type'] == 'file'):
                    for k1,v1 in v['items']['properties'].items():
                        handle_param(k1, v1, indent+"  ")
                else:
                    handle_param("item", v['items'], indent+"  ")
            w.write(indent+"</repeat>\n")
        else:
            w.write(indent+"<param ")
            w.write("name=\"%s\" " % k)
            w.write("type=\"")
            if v['type'] == 'integer':
                w.write("integer")
            elif v['type'] == 'number':
                w.write("float")
            elif v['type'] == 'string':
                w.write("text")
            elif v['type'] == 'boolean':
                w.write("boolean")
            elif v['type'] == 'file' or ('_type' in v and v['_type'] == 'file'):
                w.write("data")
            w.write("\" ")
            w.write("/>\n")

    for k,v in t.tool['inputs']['properties'].items():
        handle_param(k, v,  "    ")

    w.write("  </inputs>\n")

    w.write("  <outputs>\n")
    for k,v in t.tool['outputs']['properties'].items():
        w.write("    <data ")
        w.write("name=\"%s\" " % k)
        w.write("format=\"%s\" " % "text")
        if 'adapter' in v and 'glob' in v['adapter']:
            if 'stdout' in t.tool['adapter'] and t.tool['adapter']['stdout'] == v['adapter']['glob']:
                stdout_param = k
            else:
                w.write("from_work_dir=\"%s\" " % v['adapter']['glob'])
        w.write("/>\n")

    w.write("  </outputs>\n")

    adapter = t.tool["adapter"]
    adapters = [{"order": [-1000000],
                 "value": adapter['baseCmd']
                }]

    w.write("  <command>")

    def adapt(k, v):
        if 'adapter' in v:
            va = v['adapter']
            p = va['prefix'] if 'prefix' in va else ''
            s = va['separator'] if 'separator' in va else ''
            if v['type'] == 'array':
                if 'itemSeparator' in va:
                    val = "%s%s#for $i, $v in enumerate(${%s})##if $i!=0#%s#end if#$v#endfor#" % (p, s, k, va["itemSeparator"])
                else:
                    val = "#for $v in ${%s}# \"%s%s$v\" #end for#" % (k, p, s)
                adapters.append({"order": [va['order']] if 'order' in va else [10000000],
                                "value": val})
            else:
                adapters.append({"order": [va['order']] if 'order' in va else [10000000],
                                "value": "%s%s${%s}" % (p, s, k)})

    if "args" in adapter:
        for i, a in enumerate(adapter["args"]):
            a = copy.copy(a)
            if "order" in a:
                a["order"] = [a["order"]]
            else:
                a["order"] = [1000000]
            adapters.append(a)

    for k,v in t.tool['inputs']['properties'].items():
        adapt(k, v)

    adapters.sort(key=lambda a: a["order"])

    for f in tool.flatten([a["value"] for a in adapters]):
        if isinstance(f, dict):
            if "$job" in f:
                print >>sys.stderr, "WARNING: $job not supported yet"
            if "$expr" in f:
                print >>sys.stderr, "ERROR: $expr not supported"
        else:
            w.write(f)
            w.write(" ")

    if stdout_param:
        w.write("&gt; ${%s}" % stdout_param)
    w.write("</command>\n")

    w.write("</tool>\n")

if __name__ == "__main__":
    sys.exit(main())
