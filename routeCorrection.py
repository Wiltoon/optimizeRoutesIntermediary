from classes.types import *
from rotineIntermediary import *

def main():
    T = 3
    methods = ["kpprrf"]
    cities = ["pa-0"]
    qtdInstances = 3
    for method in methods:
        for city in cities:
            for i in range(qtdInstances):
                instanceName = "cvrp-0-"+city.split('-')[0]+"-"+str(i)+".json"
                solutionInitial = "resources/"+method+"/"+city+"/"+instanceName
                path_instance = "inputs/"+city+"/"+instanceName
                instance = CVRPInstance.from_file(path_instance)
                solution = CVRPSolution.from_file(solutionInitial)
                new_solution = rotineIntermediary(instance, solution, T)
                # compareSolutions(instance, solution, new_solution)
                

if __name__ == '__main__':
   main()