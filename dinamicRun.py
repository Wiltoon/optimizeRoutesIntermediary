from collections import deque
from itertools import combinations
import time

from tqdm import tqdm

from src.operations import *
from src.dinamic import *
from src.computeDistances import *
from precompilerDinamic import createBatchsPerPackets, separateBatchs
from src.classes.types import *
from src.classes.distances import *
from src.plot_solution import *

def solveDynamic(instance: CVRPInstance, num_lotes, deliveries, vehiclesUseds, md, TT, org):
    """
    Cada lote será separado na quantidade desejada e inserida no problema 
    """
    batchs = separateBatchs(instance, num_lotes)
    NUM_LOTE = 0
    # scores = []
    # print(batchs)
    for batch in batchs:
        routingBatchs(
            vehiclesPossibles = vehiclesUseds,
            batch = deque(batch),
            instance = instance,
            matrix = md, 
            T = TT,
            deliveries = deliveries,
            decrease = org
        )
        solution = buildSolution(instance, vehiclesUseds)
        # print("BATCH N = " + str(NUM_LOTE+1))
        NUM_LOTE += 1
    
    # print(calculateSolutionMatrix(solution, md))
    # scores.append(calculateSolutionMatrix(solution, md))
    # GERAR RESULTADO PARCIAL?
    # plot_cvrp_solution_routes(solution)
    return solution

def solveDynamicBatch(instance: CVRPInstance, num_lotes, deliveries, vehiclesUseds, md, TT, order):
    """
    Cada lote será separado na quantidade desejada e inserida no problema 
    """
    # batchs = separateBatchs(instance, num_lotes)
    batchs = createBatchsPerPackets(instance.deliveries, 75)
    NUM_LOTE = 0
    vehicles = []
    soma = 0
    for batch in tqdm(batchs, desc="DESPACHANDO LOTES"):
        # print("LOTE "+str(NUM_LOTE)+":",end=" ")
        routingBatchs(
            vehiclesPossibles = vehiclesUseds,
            batch = deque(batch),
            instance = instance,
            matrix = md, 
            T = TT,
            deliveries = deliveries,
            decrease = order
        )
        # print(vehiclesUseds)
        vehicles_aux = despatchVehicles(instance, vehiclesUseds, deliveries, 174)
        # print("VEHICLES DESPACHADOS!")
        # print(vehiclesUseds)
        # print("PACOTES EM ROTAS: "+str(len(deliveries)))
        for vehi in vehicles_aux:
            soma += len(vehi.deliveries)
            vehicles.append(vehi)
        # print("BATCH N = " + str(NUM_LOTE+1))
        NUM_LOTE += 1
        # print(len(vehicles))
    # print(vehiclesUseds)
    vehicles_aux = despatchVehicles(instance, vehiclesUseds, deliveries, 0)
    for vehicle in vehicles_aux:
        vehicles.append(vehicle)
        soma += len(vehicle.deliveries)
    # print("PACOTES COM ROTA: "+str(soma))
    # print("PACOTES SEM ROTA: "+str(len(deliveries)))
    solution = CVRPSolution(name = instance.name, vehicles = vehicles)
    return solution

def despatchVehicles(instance, vehiclesUseds, deliverys, capacityMax) -> List[CVRPSolutionVehicle]:
    # print("LIMITE INFERIOR :" + str(capacityMax))
    idVehiclesDespatchs = []
    vehicles = []
    for k, v in vehiclesUseds.items():
        capacity = 0
        decorrer = v[0][1:]
        for d in decorrer:
            capacity += instance.deliveries[d].size
        if capacity > capacityMax:
            idVehiclesDespatchs.append(k)
    # print("IDS ROTES")
    # print(idVehiclesDespatchs)
    for id_route in idVehiclesDespatchs:
        vehicle = []
        percorrer = vehiclesUseds[id_route][0][1:]
        for id_pack in percorrer:
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
        # print("OO QUE E ISSO:?")
        # print(vehiclesUseds[id_route][0]))
        # print(percorrer)
        for demand in percorrer:
            deliverys.remove(demand)
        # print("Vehicle Despatch: ", len(vehicles))
        del vehiclesUseds[id_route]
    return vehicles


def buildSolution(instance: CVRPInstance, vehicles_occupation):
    """Cria a solução e o nome do arquivo json"""
    # dir_out = "out/dinamic/"+city+"/"
    # nameFile = "d"+instance.name+"batch-"+str(NUM_LOTE)+".json"
    # filename = dir_out + nameFile
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
    return solution #, filename

def solveD(instance, solution, matrix_distance, T, NUM_LOTES, org, SCOREMIN):
    """CASO 2 se solution = -1 e CASO 1 caso haja uma solution entregue"""
    deliveries = []
    if solution == "estatico":
        # print("CASO 2")
        # print(len(points))
        vPossibles = {}
        st = time.time()
        new_solution = solveDynamic(
            instance = instance, 
            num_lotes = NUM_LOTES, 
            deliveries = deliveries, 
            vehiclesUseds = vPossibles, 
            md = matrix_distance,
            TT = T,
            org = org
        )
        # vehiclesPossibles = reduceVehicles(
        #   instance, vehiclesPossibles, matrix_distance)
        # print(vehiclesPossibles)
        vPossibles = createVehiclesPossibles(new_solution)
        allin = [f for f in range(len(vPossibles))]
        combs = [p for p in list(combinations(allin,2))]
        for i in range(10):
            for comb in combs:
                vPossibles[comb[0]], vPossibles[comb[1]] = twoOptStarModificated(
                    vPossibles[comb[0]],
                    vPossibles[comb[1]],
                    matrix_distance,
                    instance
                )
        fn = time.time()
        time_exec = float(fn-st)                
        new_solution = solutionJsonWithTimeT(time_exec, instance, vPossibles)
        score = calculateSolutionMatrix(new_solution, matrix_distance)
        if score < SCOREMIN:
            SCOREMIN = score
            print(score+" "+len(vPossibles))
        return new_solution
    elif solution == "dinamico":
        
        vPossibles = {}
        # vai receber 1 lote de cada vez
        new_solution = solveDynamicBatch(
            instance = instance, 
            num_lotes = NUM_LOTES, 
            deliveries = deliveries, 
            vehiclesUseds = vPossibles, 
            md = matrix_distance,
            TT = T,
            order = org
        )
        score = calculateSolutionMatrix(new_solution, matrix_distance)
        print(str(score) + " " + str(len(new_solution.vehicles)), end=" ")
        return new_solution
        # print("CASO 1")
        # vehiclesPossibles = 0 # criar o dicionario a partir da solução



# TEMOS DOIS CASOS!!!
# 1 CASO = TEMOS UMA SOLUÇÃO INICIAL COMO ELA DEVERA COMEÇAR??
# 2 CASO = TEMOS NENHUMA SOLUÇÃO INICIAL E GERAMOS TUDO
def executeDinamic():
    varT = [30,31]
    varLOTES = [10,11]
    osrm_config = OSRMConfig(
        host="http://ec2-34-222-175-250.us-west-2.compute.amazonaws.com"
    )
    cities = ["rj-0"]
    # mode = "estatico"
    mode = "dinamico"
    se = [90,120]
    organisation = [None, True, False] # sem ordem, ordem decrescente, ordem crescente
    startInstance = se[0]
    endInstance = se[1]
    for city in cities:
        for day in range(startInstance, endInstance):
            instanceName = "cvrp-0-"+city.split('-')[0]+"-"+str(day)+".json"
            # print(instanceName)
            path_instance = "inputs/"+city+"/"+instanceName
            instance = CVRPInstance.from_file(path_instance)
            points = [instance.origin] + [d.point for d in instance.deliveries]
            matrix_distance = calculate_distance_matrix_m(
                points, osrm_config
            )
            for T in range(varT[0], varT[1]):
                for org in organisation:
                    for NUM_LOTES in range(varLOTES[0], varLOTES[1]):
                        # print("Para T, NUM_LOTES, ORG = "+str(T)+"-"+str(NUM_LOTES) + nameOrg(org))
                        name = "cvrp-0-"+city.split('-')[0]+"-"+str(day)+"-T-"+str(T)+"-L-"+str(NUM_LOTES)+"-O-"+nameOrg(org)
                        filename = "out/srn/"+city+"/"+name+".json"
                        scoremin = 999999999
                        solution = solveD(instance, mode, matrix_distance, T, NUM_LOTES, org, scoremin)
                        solution.to_file(filename)
                print(" ")

def nameOrg(value):
    if value == None:
        return "S"
    elif value == True:
        return "D"
    else:
        return "C"
    
if __name__ == '__main__':
    executeDinamic()