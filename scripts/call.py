#!/usr/bin/env python3

import argparse
import collections
import functools
import networkx as nx

def node_name (name):
  return "\"{%s}\"" % name

#################################
# Find the graph node for a name
#################################
def find_nodes (G, name):
  n_name = node_name (name)
  return [n for n, d in G.nodes(data=True) if n_name in d.get('label', '')]


##################################
# Main function
##################################
if __name__ == '__main__':
  parser = argparse.ArgumentParser ()
  parser.add_argument ('-d', '--dot', type=str, required=True, help="Path to dot-file representing the graph.")
  parser.add_argument ('-o', '--out', type=str, required=True, help="Path to output file containing distance for each node.")
  parser.add_argument ('-s', '--sources', type=str, required=True, help="Source functions.")
  parser.add_argument ('-ft', '--ftargets', type=str, required=False, help="Path to file of target functions.")

  args = parser.parse_args ()

  G = nx.DiGraph(nx.drawing.nx_pydot.read_dot(args.dot))
  # Process as ControlFlowGraph
  caller = ""
  cg_distance = {}
  bb_distance = {}
  with open(args.out, "w") as out, open(args.sources, "r") as f:
    nodes = []
    for fn in f.readlines():
      nodes.extend(find_nodes(G, fn.strip()))
    todo = list(set(nodes))

    done = []
    while len(todo) > 0:
      tmp = todo.pop()
      outs = G.out_edges(tmp)
      for o in outs:
        if o[1] not in done and o[1] not in todo:
          todo.append(o[1])
      done.append(tmp)
    #print('done', done)
    finals = set()
    for node, data in G.nodes(data=True):
      if node in done:
        label = data.get('label', '')
        if label != '':
          finals.add(label.strip('"{}'))
    #print(finals)

    with open(args.ftargets, 'r') as fp:
      funcs = fp.readlines()
      for func in funcs:
        tokens = func.strip().split(',')
        mangledName = tokens[0]
        finals.add(mangledName)

    #with open(args.ftargets, 'r') as fp:
    out.write('\n'.join(list(finals)))
          

