from dinamic import *
from precompilerDinamic import separateBatchs
from src.classes.types import *

def solveDynamic(instance: CVRPInstance, num_lotes, deliveries, vehiclesUseds, md, TT):
    """
    Cada lote será separado na quantidade desejada e inserida no problema 
    """
    batchs = separateBatchs(instance, num_lotes)
    for batch in batchs:
        routingBatchs(
            vehiclesPossibles = vehiclesUseds,
            batch = batch,
            instance = instance,
            matrix = md, 
            T = TT,
            deliveries = deliveries
        )
        # GERAR RESULTADO PARCIAL?

def solveD(instance, solution, osrm_config, T, city, NUM_LOTES):
    """CASO 2 se solution = -1 e CASO 1 caso haja uma solution entregue"""
    deliveries = []
    if solution == -1:
        print("CASO 2")
        matrix_distance = [[]] # montar matriz de distancia com deposito
        vehiclesPossibles = {}
        solveDynamic(
            instance = instance, 
            num_lotes = NUM_LOTES, 
            deliveries = deliveries, 
            vehiclesUseds = vehiclesPossibles, 
            md = matrix_distance,
            TT = T
        )

    else:
        print("CASO 1")
    # vehiclesPossibles = 0 # criar o dicionario a partir da solução



# TEMOS DOIS CASOS!!!
# 1 CASO = TEMOS UMA SOLUÇÃO INICIAL COMO ELA DEVERA COMEÇAR??
# 2 CASO = TEMOS NENHUMA SOLUÇÃO INICIAL E GERAMOS TUDO
def main():
    T = 3
    NUM_LOTES = 5
    osrm_config = OSRMConfig(
        host="http://ec2-34-222-175-250.us-west-2.compute.amazonaws.com"
    )
    cities = ["pa-0"]
    startInstance = 90
    endInstance = 91
    for city in cities:
        for day in range(startInstance, endInstance):
            instanceName = "cvrp-0-"+city.split('-')[0]+"-"+str(day)+".json"
            path_instance = "inputs/"+city+"/"+instanceName
            instance = CVRPInstance.from_file(path_instance)
            solveD(instance, -1, osrm_config, T, city, NUM_LOTES)