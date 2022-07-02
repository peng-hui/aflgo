#!/usr/bin/env python3

import argparse, re
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
    parser.add_argument ('-bn', '--bbnames', type=str, required=False, help="Path to file containing name for each node.")
    parser.add_argument ('-cg', '--cg_distance', type=str, help="Path to file containing call graph distance.")
    parser.add_argument ('-bc', '--bbcalls', type=str, help="Path to file containing mapping between basic blocks and called functions.")
    parser.add_argument ('-fl', '--funclocs', type=str, help="Path to file containing mapping between basic blocks and called functions.")
    args = parser.parse_args ()

    userDefinedFunctions = []
    with open(args.funclocs, 'r') as fp:
        funcs = fp.readlines()
        for func in funcs:
            tokens = func.strip().split(',')
            mangledName = tokens[0]
            userDefinedFunctions.append(mangledName)

    bbfunctionMap = {}
    with open(args.bbcalls, 'r') as fp:
        calls = fp.readlines()
        for call in calls:
            tokens = call.strip().split(',')
            if tokens[0] == '':
                continue
            mangledName = tokens[1]
            uniqueId = tokens[2] + tokens[3]
            bbfunctionMap[uniqueId] = mangledName

    targetfunctionMap = {}
    with open(args.ftargets, 'r') as fp:
        funcs = fp.readlines()
        for func in funcs:
            tokens = func.strip().split(',')
            mangledName = tokens[0]
            uniqueId = tokens[2] + tokens[1]
            targetfunctionMap[uniqueId] = mangledName
            #id filename:line+demangedFname.

    #with open(args.ftargets, 'r') as fp:
    #    ftargets = [i.split(',')[0] for i in fp.readlines()]
    target_locations = []
    with open(args.targets, 'r') as fp:
        target_locations = [i.strip() for i in fp.readlines()]
    print('target locations:', str(target_locations))
    # currently we assume we already obtain a target chain, that is, in the interesting functions, we have the targets. 
    # if a function does not contain a target, we think the function does not need to have distance metrics?
    # we use only intra-procedural analysis and award-based fitness functions.

    '''
    for each function, we construct the call graph.
    in target functions, we identify the callees.
    and then through call-graph analysis, we identify the functions need to be instrumneted
    which include, target functions, and the calees and recursive callees.

    For distance, we commpute the distance only in target functions.
    For each basic block, we compute the distance to the sub-target.
    '''


    file2BBs = {}
    with open(args.bbnames, 'r') as fp:
        for i in fp.readlines():
            i = i.strip()
            if i == '':
                continue
            tokens = i.split(':')
            if len(tokens) !=2:
                continue
            if tokens[0] not in file2BBs.keys():
                file2BBs[tokens[0]] = []
            file2BBs[tokens[0]].append(int(tokens[1]))

    for fn in file2BBs.keys():
        file2BBs[fn] = sorted(file2BBs[fn])

    def getBB(key):
        tokens = key.strip().split(':')
        ran = file2BBs[tokens[0]]
        for i in range(len(ran) - 1):
            if int(tokens[1]) in range(ran[i], ran[i+1]):
                return tokens[0] + ':' + str(ran[i])
        return tokens[0] + ':' + str(ran[-1])


    fileNumber = len(os.listdir(args.cdg))
    target_functions = []
    allCallsites = []
    distances = {}
    for n in range(fileNumber):
        astFile = join(args.ast, '%d-ast.dot' % n)
        cdgFile = join(args.cdg, '%d-cdg.dot' % n)
        with open(cdgFile, 'r') as fp:
            l = fp.readline().strip().split('"')
            nums = re.findall(r'\d+', l[1])
            t = l[1].replace(nums[0], str(int(nums[0]) + 1))
            if l[1] in targetfunctionMap.keys():
                ftarget = targetfunctionMap[l[1]]
            elif t in targetfunctionMap.keys():
                ftarget = targetfunctionMap[t]
            else:
                continue
            #print(ftarget)
            # the function is target function.
            AST = nx.DiGraph(nx.drawing.nx_pydot.read_dot(astFile))
            max_target_node = 0
            target_nodes = []

            tmp_callsites = []
            for node, data in AST.nodes(data=True):
                label = data.get('label')
                tokens = label.strip('")(').split(',')
                if not tokens[-1].startswith(':') and tokens[0] != 'UNKNOWN': # can locate the filename

                    if tokens[-1] in target_locations:
                        target_nodes.append(node)
                        allCallsites.extend(tmp_callsites)
                        tmp_callsites = []
                        #print('target node', node, tokens[-1])
                        if int(node) > max_target_node:
                            max_target_node = int(node)
                    elif 'CALL' in label and (tokens[-1] + tokens[1]) in bbfunctionMap.keys() and bbfunctionMap[tokens[-1] + tokens[1]] in userDefinedFunctions: #functionMap1.keys():
                        tmp_callsites.append(bbfunctionMap[tokens[-1] + tokens[1]])
            

            CDG = nx.DiGraph(nx.drawing.nx_pydot.read_dot(cdgFile))
            for node, data in CDG.nodes(data=True):
                if int(node) > max_target_node:
                    continue
                label = data.get('label')
                tokens = label.strip('")(').split(',')
                if not tokens[-1].startswith(':') and tokens[0] != 'UNKNOWN': # can locate the filename
                    #if tokens[-1] in bbnames:
                    distance = -1
                    for target in target_nodes:
                        try:
                            distance = nx.dijkstra_path_length (CDG, node, target)
                        except nx.NetworkXNoPath:
                            pass
                    if distance != -1:
                        distances[getBB(tokens[-1])] = distance

    with open(join(args.out, 'distance.cdg.txt'), 'w') as fp:
        fp.write('\n'.join(["%s,%d" % (key, val) for (key, val) in distances.items()]))
    #allCallsites.extend(list(targetfunctionMap.values()))
    allCallsites = list(set(allCallsites))
    with open(join(args.out, 'mangled-callsites.txt'), 'w') as fp:
        fp.write('\n'.join(allCallsites))

