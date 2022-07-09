from src.classes.distances import *
from src.classes.types import *
from dinamicRun import *


def calcularDistancias():
    varT = [30,31]
    varLOTES = [1,2]
    osrm_config = OSRMConfig(
        host="http://ec2-34-222-175-250.us-west-2.compute.amazonaws.com"
    )
    cities = ["rj-0"]
    se = [90,97]
    organisation = [None, True, False] # sem ordem, ordem decrescente, ordem crescente
    startInstance = se[0]
    endInstance = se[1]
    for city in cities:
        for day in range(startInstance, endInstance):
            instanceName = "cvrp-0-"+city.split('-')[0]+"-"+str(day)+".json"
            print(instanceName)
            path_instance = "inputs/"+city+"/"+instanceName
            instance = CVRPInstance.from_file(path_instance)
            points = [instance.origin] + [d.point for d in instance.deliveries]
            matrix_distance = calculate_distance_matrix_m(
                points, osrm_config
            )
            for T in range(varT[0], varT[1]):
                for org in organisation:
                    for NUM_LOTES in range(varLOTES[0], varLOTES[1]):
                        print("Para T, NUM_LOTES, ORG = "+str(T)+"-"+str(NUM_LOTES) + nameOrg(org))
                        name = "cvrp-0-"+city.split('-')[0]+"-"+str(day)+"-T-"+str(T)+"-L-"+str(NUM_LOTES)+"-O-"+nameOrg(org)
                        filename = "out/srn/"+city+"/"+name+".json"
                        solution = CVRPSolution.from_file(filename)
                        score = calculateSolutionMatrix(solution, matrix_distance)
                        print(score,len(solution.vehicles),T,NUM_LOTES,nameOrg(org))
                        

if __name__ == '__main__':
    calcularDistancias()