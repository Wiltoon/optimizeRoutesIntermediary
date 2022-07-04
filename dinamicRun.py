from collections import deque

from src.dinamic import *
from src.computeDistances import *
from precompilerDinamic import separateBatchs
from src.classes.types import *
from src.classes.distances import *
from src.plot_solution import *

def solveDynamic(instance: CVRPInstance, num_lotes, deliveries, vehiclesUseds, md, TT, city):
    """
    Cada lote será separado na quantidade desejada e inserida no problema 
    """
    batchs = separateBatchs(instance, num_lotes)
    NUM_LOTE = 0
    # print(batchs)
    for batch in batchs:
        routingBatchs(
            vehiclesPossibles = vehiclesUseds,
            batch = deque(batch),
            instance = instance,
            matrix = md, 
            T = TT,
            deliveries = deliveries
        )
        solution, filename = buildSolution(instance, vehiclesUseds, NUM_LOTE, city)
        solution.to_file(filename)
        print(calculateSolutionMatrix(solution, md))
        NUM_LOTE += 1
        # GERAR RESULTADO PARCIAL?
        plot_cvrp_solution(solution)



def buildSolution(instance: CVRPInstance, vehicles_occupation, NUM_LOTE, city):
    """Cria a solução e o nome do arquivo json"""
    dir_out = "out/dinamic/"+city+"/"
    nameFile = "d"+instance.name+"batch-"+str(NUM_LOTE)+".json"
    filename = dir_out + nameFile
    name = instance.name
    vehicles = []
    for k, v in vehicles_occupation.items():
        vehicle = []
        dep = 0
        for id_pack in v[0]:
            if dep == 0:
                dep += 1
                continue
            else:
                point = Point(
                    lng=instance.deliveries[id_pack].point.lng, 
                    lat=instance.deliveries[id_pack].point.lat
                )
                delivery = Delivery(
                    id_pack,
                    point,
                    instance.deliveries[id_pack].size,
                    instance.deliveries[id_pack].idu
                )
                vehicle.append(delivery)
        vehicleConstruct = CVRPSolutionVehicle(origin=instance.origin, deliveries=vehicle)
        vehicles.append(vehicleConstruct)
    solution = CVRPSolution(name=name, vehicles=vehicles)
    return solution, filename

def solveD(instance, solution, osrm_config, T, city, NUM_LOTES):
    """CASO 2 se solution = -1 e CASO 1 caso haja uma solution entregue"""
    deliveries = []
    if solution == -1:
        print("CASO 2")
        points = [instance.origin] + [d.point for d in instance.deliveries]
        matrix_distance = calculate_distance_matrix_m(
            points, osrm_config
        )
        print(len(points))
        vehiclesPossibles = {}
        solveDynamic(
            instance = instance, 
            num_lotes = NUM_LOTES, 
            deliveries = deliveries, 
            vehiclesUseds = vehiclesPossibles, 
            md = matrix_distance,
            TT = T,
            city = city
        )
    else:
        print("CASO 1")
        # vehiclesPossibles = 0 # criar o dicionario a partir da solução



# TEMOS DOIS CASOS!!!
# 1 CASO = TEMOS UMA SOLUÇÃO INICIAL COMO ELA DEVERA COMEÇAR??
# 2 CASO = TEMOS NENHUMA SOLUÇÃO INICIAL E GERAMOS TUDO
def executeDinamic(T, NUM_LOTES):

    osrm_config = OSRMConfig(
        host="http://ec2-34-222-175-250.us-west-2.compute.amazonaws.com"
    )
    cities = ["pa-0"]
    startInstance = 90
    endInstance = 91
    for city in cities:
        for day in range(startInstance, endInstance):
            instanceName = "cvrp-0-"+city.split('-')[0]+"-"+str(day)+".json"
            print(instanceName)
            path_instance = "inputs/"+city+"/"+instanceName
            instance = CVRPInstance.from_file(path_instance)
            solveD(instance, -1, osrm_config, T, city, NUM_LOTES)

if __name__ == '__main__':
    varT = [15,16]
    varLOTES = [4,5]
    for T in range(varT[0], varT[1]):
        for NUM_LOTES in range(varLOTES[0], varLOTES[1]):
            executeDinamic(T, NUM_LOTES)