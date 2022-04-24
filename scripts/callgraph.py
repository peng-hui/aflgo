#!/usr/bin/env python3

import argparse
import collections
import functools
import networkx as nx
import os
from os.path import join
##################################
# Main function
##################################
if __name__ == '__main__':
    parser = argparse.ArgumentParser ()
    parser.add_argument ('-d', '--dot', type=str, required=False, help="Path to dot-file representing the graph.")
    parser.add_argument ('-t', '--targets', type=str, required=False, help="Path to file specifying Target nodes.")
    parser.add_argument ('-ft', '--ftargets', type=str, required=False, help="Path to file of target functions.")
    parser.add_argument ('-a', '--ast', type=str, required=False, help="Path to file specifying AST dot files/graphs .")
    parser.add_argument ('-c', '--cdg', type=str, required=False, help="Path to file specifying CDG dot files/graphs .")
    parser.add_argument ('-o', '--out', type=str, required=False, help="Path to output file containing distance for each node.")
    parser.add_argument ('-n', '--names', type=str, required=False, help="Path to file containing name for each node.")
    parser.add_argument ('-cg', '--cg_distance', type=str, help="Path to file containing call graph distance.")
    parser.add_argument ('-bc', '--bbcalls', type=str, help="Path to file containing mapping between basic blocks and called functions.")
    parser.add_argument ('-fl', '--funclocs', type=str, help="Path to file containing mapping between basic blocks and called functions.")
    args = parser.parse_args ()


    functionMap = {}
    with open(args.bbcalls, 'r') as fp:
        calls = fp.readlines()
        for call in calls:
            tokens = call.strip().split(',')
            mangledName = tokens[1]
            uniqueId = tokens[2] + tokens[3]
            functionMap[uniqueId] = mangledName
    functionMap1 = {}
    userDefinedFunctions = []
    with open(args.funclocs, 'r') as fp:
        funcs = fp.readlines()
        for func in funcs:
            tokens = func.strip().split(',')
            mangledName = tokens[0]
            uniqueId = tokens[2] + tokens[1]
            userDefinedFunctions.append(mangledName)
            #functionMap1[mangledName] = uniqueId
            functionMap1[uniqueId] = mangledName

    target_locations = []
    with open(args.targets, 'r') as fp:
        target_locations = [i.strip() for i in fp.readlines()]
    
    '''
    for each function, we construct the call graph.
    '''
    CG = nx.DiGraph()
    fileNumber = len(os.listdir(args.cdg))
    target_nodes = []
    target_functions = []
    for n in range(fileNumber):
        astFile = join(args.ast, '%d-ast.dot' % n)
        cdgFile = join(args.cdg, '%d-cdg.dot' % n)
        with open(cdgFile, 'r') as fp:
            l = fp.readline().strip().split('"')
            if len(l) != 3:
                continue
            if l[1] not in functionMap1.keys():
                continue
            
        AST = nx.DiGraph(nx.drawing.nx_pydot.read_dot(astFile))
        #caller = AST.name.strip()
        caller = functionMap1[AST.name.strip()] # get mangled name
        if caller not in CG.nodes():
            CG.add_node(caller)

        allCallsites = {}
        has_target = False
        for node, data in AST.nodes(data=True):
            label = data.get('label')
            tokens = label.strip('")(').split(',')
            if not tokens[-1].startswith(':') and tokens[0] != 'UNKNOWN': # can locate the filename
                if 'CALL' in label and (tokens[-1] + tokens[1]) in functionMap.keys() and functionMap[tokens[-1] + tokens[1]] in userDefinedFunctions: #functionMap1.keys():
                    allCallsites[node] = tokens[-1] + tokens[1]
                if tokens[-1] in target_locations:
                    has_target = True
                    target_nodes.append(node + "," + tokens[-1] + "," + tokens[1])
                    target_functions.append(caller)

        CDG = nx.DiGraph(nx.drawing.nx_pydot.read_dot(cdgFile))
        allRelatedCallsites = []
        for node, data in CDG.nodes(data=True):
            label = data.get('label')
            tokens = label.strip('")(').split(',')
            if not tokens[-1].startswith(':') and tokens[0] != 'UNKNOWN': # can locate the filename
                if 'CALL' in label and (tokens[-1] + tokens[1]) in functionMap.keys() and functionMap[tokens[-1] + tokens[1]] in userDefinedFunctions: #functionMap1.keys():
                    allRelatedCallsites.append(node)

        # sources might not be functon entry.
        sources = [n for n in CDG.nodes() if CDG.in_degree(n) == 0]
        print(len(sources), 'sources')
        print(len(allRelatedCallsites), 'callsites')
        if len(allRelatedCallsites) == 0 or len(sources) == 0:
            continue

        shortestDistances = {}
        for callId in allRelatedCallsites:
            calleeName = allCallsites[callId]
            mangledCalleeName = functionMap[calleeName]
            #definitionCalleeName = functionMap1[mangledCalleeName]
            for source in sources:
                try:
                    distance = nx.dijkstra_path_length (CDG, source, callId)
                    if mangledCalleeName in shortestDistances.keys():
                        shortestDistances[mangledCalleeName] = min(shortestDistances[mangledCalleeName], distance)
                    else:
                        shortestDistances[mangledCalleeName] = distance
                except nx.NetworkXNoPath:
                    pass

        for (callId, calleeName) in allCallsites.items():
            mangledCalleeName = functionMap[calleeName]
            if mangledCalleeName not in shortestDistances.keys():
                shortestDistances[mangledCalleeName] = 0
        for (callee, dis) in shortestDistances.items():
            print(callee, dis)
            if callee not in CG.nodes():
                CG.add_node(callee)
            CG.add_edge(caller, callee, weight=dis)

        with open(join(args.out, 'cg-distance-%s.txt' % caller), 'w') as fp:
            fp.write('\n'.join(["%s,%f" % (key, val) for (key, val) in shortestDistances.items()]))
    if len(target_functions) == 0:
        print('no target function found, and should exit')
        exit(0)

    out = open(args.cg_distance, 'w')
    for func in CG.nodes():
        dd = - 1
        d = 0.0
        i = 0
        for tf in target_functions:
            try:
                shortest = nx.dijkstra_path_length (CG, func, tf)
                d += 1.0/(1.0 + shortest)
                i += 1
            except nx.NetworkXNoPath:
                    pass
        if d != 0 and (dd == -1 or dd > i / d):
            dd = i / d
        if dd != -1:
            out.write(func + "," + str(dd) + "\n")
