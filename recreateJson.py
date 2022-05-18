import json
from src.classes.types import * 
from collections import defaultdict

def generateOutJson(solution: CVRPSolution, out_path: str):
    solution.to_file(out_path)

def recreate(names):
    method = "lkh3"
    city = "pa-0"
    in_dir_path = "inputs/"+city+"/"
    out_dir = "resources/"+method+"/"+city+"/"
    for name in names:
        input = in_dir_path+name
        instance = CVRPInstance.from_file(input)
        for i in range(len(instance.deliveries)):
            instance.deliveries[i].idu = i
        instance.to_file(input)
        packs = defaultdict(list)
        used = defaultdict(list)
        for idu in range(len(instance.deliveries)):
            packs[instance.deliveries[idu].id].append(idu)
            used[instance.deliveries[idu].id].append(False)
        out = out_dir + name
        solution = CVRPSolution.from_file(out)
        for v in solution.vehicles:
            for d in v.deliveries:
                # print("packs = " + str(packs[d.id]))
                # print("used = " + str(used[d.id]))
                for u in range(len(used[d.id])):
                    if used[d.id][u] == False:
                        used[d.id][u] = True
                        d.idu = packs[d.id][u]
                        break
        new_vehicles = []
        for v in solution.vehicles:
            new_deliveries = []
            for d in v.deliveries:
                if d.id != "DEPOSITO":
                    new_deliveries.append(d)
            ori = v.origin
            new_tour = CVRPSolutionVehicle(origin=ori, deliveries=new_deliveries)
            new_vehicles.append(new_tour)
        solution.vehicles = new_vehicles
        generateOutJson(solution, out)

if __name__ == '__main__':
    numDays = 20
    city = "pa-0"
    instances = []
    for i in range(numDays):
        instance = "cvrp-0-"+city.split('-')[0]+"-"+str(i)+".json"
        instances.append(instance)
    recreate(instances)