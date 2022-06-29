from src.classes.types import *

def separateBatchs(instance: CVRPInstance, num_batchs):
    """Separa os pacotes em vários lotes"""
    n_packs_per_batch = int(len(instance.deliveries)/num_batchs)
    return createBatchsPerPackets(instance.deliveries, n_packs_per_batch)

def createBatchsPerPackets(deliveries, x: int):
    """Criar lotes pelo numero de pacotes"""
    final_list = lambda deliveries, x: [deliveries[i:i+x] for i in range(0, len(deliveries), x)]
    batchs = final_list(deliveries, x)
    return batchs

