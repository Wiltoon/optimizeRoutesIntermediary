import json
from .classes.types import * 
from collections import defaultdict

def generateOutJson(solution: CVRPSolution):
    print(solution)

def recreate(inputs, outs):
    for input in inputs:
        instance = CVRPInstance.from_file(input)
        packs = defaultdict(list)
        used = defaultdict(list)
        for idu in range(len(instance.deliveries)):
            packs[instance.deliveires[idu].id].append(idu)
            used[instance.deliveires[idu].id].append(False)
    for out in outs:
        solution = CVRPSolution.from_file(out)
        for v in solution.vehicles:
            for d in v.deliveries:
                for u in range(len(used[d.id])):
                    if used[d.id][u] == False:
                        used[d.id][u] = True
                        d.idu = packs[d.id][u]
        generateOutJson(solution)

if __name__ == '__main__':
    recreate()