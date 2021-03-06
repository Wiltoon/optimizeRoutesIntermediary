import json
from src.classes.types import * 
from collections import defaultdict

def generateOutJson(solution: CVRPSolutionKpprrf, out_path: str):
    solution.to_file(out_path)

def recreate(names, city, method):
    in_dir_path = "inputs/"+city+"/"
    out_dir = "resources/"+method+"/"+city+"/"
    for name in names:
        try:
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
            solution = CVRPSolutionKpprrf.from_file(out)
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
        except Exception as e:
            print(e)
            pass

if __name__ == '__main__':
    method = "kvprfhete"
    numDays = 30
    city = "pa-0"
    instances = []
    for i in range(90, 90+numDays):
        instance = "cvrp-0-"+city.split('-')[0]+"-"+str(i)+".json"
        instances.append(instance)
    recreate(instances, city, method)