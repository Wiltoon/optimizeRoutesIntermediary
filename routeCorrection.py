from src.classes.types import *
from src.rotineIntermediary import *

def main():
    T = 3
    osrm_config = OSRMConfig(
        host="http://ec2-34-222-175-250.us-west-2.compute.amazonaws.com"
    )
    methods = ["ccpmiphomo"]
    cities = ["pa-0"]
    qtdInstances = 30
    for method in methods:
        for city in cities:
            for i in range(90,90+qtdInstances):
                instanceName = "cvrp-0-"+city.split('-')[0]+"-"+str(i)+".json"
                print("SOLUÇÃO =>" + instanceName)
                solutionInitial = "resources/"+method+"/"+city+"/"+instanceName
                path_instance = "inputs/"+city+"/"+instanceName
                try:
                    instance = CVRPInstance.from_file(path_instance)
                    solution = CVRPSolution.from_file(solutionInitial)
                    new_solution = rotineIntermediary(
                        instance, solution, osrm_config, T, city, method
                        )
                except Exception as ex:
                    print(ex)
                # new_solution.to_file("out/"+method+"/"+city+"/"+instanceName)
                # compareSolutions(instance, solution, new_solution)

if __name__ == '__main__':
   main()