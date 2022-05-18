# Here we have 2opt* with aim of swap 1 route's pack for another route's pack 
from .classes.types import *

# Aqui é calculado a perda e o ganho de distância ao trocar 
# o pacote r1[i] pelo r2[j] 
def compensationSwap(md, r1, r2, i, j):
    if i != (len(r1)-1):
        if i-1 == 0:
            gain = md[r1[i-1]][r2[j]+1] + md[r2[j]+1][r1[i+1]+1]
            lose = md[r1[i-1]][r1[i]+1] + md[r1[i]+1][r1[i+1]+1]
        else:
            gain = md[r1[i-1]+1][r2[j]+1] + md[r2[j]+1][r1[i+1]+1]
            lose = md[r1[i-1]+1][r1[i]+1] + md[r1[i]+1][r1[i+1]+1]
    else:
        if i-1 == 0:
            gain = md[r1[i-1]][r2[j]+1]
            lose = md[r1[i-1]][r1[i]+1]
        else:
            gain = md[r1[i-1]+1][r2[j]+1]
            lose = md[r1[i-1]+1][r1[i]+1]
    return gain, lose

def constraintCapacity(instance, route, left, arrive: Delivery):
    CAP = instance.vehicle_capacity
    DEP = 0
    total = 0 
    for i in route:
        if DEP == 0:
            DEP += 1
        else:
            total += instance.deliveries[i].size
    sizeLeft = instance.deliveries[route[left]].size
    packSize = arrive.size
    # print("Total = " +str(total))
    # print("sizeLife = "+str(sizeLeft))
    # print("packSize = "+str(packSize))
    return total - sizeLeft + packSize <= CAP

def constraintCapacityAdd(instance, route, arrive: Delivery):
    CAP = instance.vehicle_capacity
    DEP = 0
    total = 0 
    # print(route)
    # print(arrive.size)
    for i in route:
        if DEP == 0:
            DEP += 1
        else:
            total += instance.deliveries[i].size
    packSize = arrive.size
    # print("Total = " +str(total))
    # print("packSize = "+str(packSize))
    return total + packSize <= CAP


def swapPossible(instance, route1, route2, p1, p2):
    # somar todas as cargas da rota1 - packet1 + packet2
    return constraintCapacity(
        instance, 
        route1, p1, instance.deliveries[route2[p2]]) and constraintCapacity(
            instance, 
            route2, p2, instance.deliveries[route1[p1]])

def computeCompensationSwap(md, route1, route2, p1, p2):
    gain1, lose1 = compensationSwap(md, route1, route2, p1, p2)
    gain2, lose2 = compensationSwap(md, route2, route1, p2, p1)
    loseSwap = lose1 + lose2
    gainSwap = gain1 + gain2
    return round((gainSwap)/1_000,3), round((loseSwap)/1_000, 3)

def twoOptStar(route1, route2, md, instance):
    for p1 in range(1,len(route1)):
        for p2 in range(1,len(route2)):
            if swapPossible(instance, route1, route2, p1, p2):
                gainSwap, loseSwap = computeCompensationSwap(
                    md, route1, route2, p1, p2)
                if loseSwap > gainSwap:
                    new_route1 = [
                        route1[i] 
                        for i in range(len(route1)) 
                        if i != p1
                    ]
                    new_route1.insert(p1, route2[p2])
                    new_route2 = [
                        route2[j] 
                        for j in range(len(route2)) 
                        if j != p2
                    ]
                    new_route2.insert(p2, route1[p1])
                    route1 = new_route1.copy()
                    route2 = new_route2.copy()
    return route1, route2

def swapPacks(
    matrix_distance, 
    instance: CVRPInstance, 
    route1: list, route2: list, 
    p1: int, p2: int) -> RoutePossible:
    if swapPossible(instance, route1, route2, p1, p2):
        select = [2, 1]
        gainSwap, loseSwap = computeCompensationSwap(
                    matrix_distance, route1, route2, p1, p2)
        if loseSwap > gainSwap:
            new_route1 = [
                route1[i] 
                for i in range(len(route1)) 
                if i != p1
            ]
            new_route1.insert(p1, route2[p2])
            new_route2 = [
                route2[j] 
                for j in range(len(route2)) 
                if j != p2
            ]
            new_route2.insert(p2, route1[p1])
            gain = round((loseSwap - gainSwap), 3)
            possibleSwap = RoutePossible(
                new_route1,
                new_route2,
                gain,
                select)
        else:
            return None # lose < gain
    else:
        return None # nao respeita capacidade
    return possibleSwap

def compensationInsertInRoute(
    md,
    rd,
    p_insert, # 152 -> 153 
    i_destiny # index = 3 
    ):
    # pacote da posição p_insert do ro está indo para o rd
    # ro[p_insert] -> rd[p_destiny]
    gainDistanceTotal = 0
    lose = 0
    gain = 0
    if i_destiny < (len(rd)-1): # ultimo elemento não tem perda
        if i_destiny == 1:
            lose += md[rd[i_destiny-1]][rd[i_destiny]+1]
            gain += md[rd[i_destiny-1]][p_insert+1]
            gain += md[p_insert+1][rd[i_destiny]+1]
        else:
            lose += md[rd[i_destiny-1]+1][rd[i_destiny]+1]
            gain += md[rd[i_destiny-1]+1][p_insert+1]
            gain += md[p_insert+1][rd[i_destiny]+1]
    else:
        if i_destiny == 1:
            gain += md[rd[i_destiny-1]][p_insert+1]
        else:
            gain += md[rd[i_destiny-1]+1][p_insert+1]
    gainDistanceTotal = round((lose - gain)/1_000,3)
    return gainDistanceTotal

def compensationRemoveInRoute(
    md, 
    ro, 
    i_remove # index -> ro[i_remove] = 152 -> 153 
):
    lose = 0 # ... calcular as arestas perdidas
    gain = 0 # ... calcular as arestas adicionadas
    if i_remove < (len(ro)-1): # ultimo elemento não tem perda
        if i_remove == 1:
            gain += md[ro[i_remove-1]][ro[i_remove+1]+1]
            lose += md[ro[i_remove-1]][ro[i_remove]+1]
            lose += md[ro[i_remove]+1][ro[i_remove+1]+1]
        else:
            gain += md[ro[i_remove-1]+1][ro[i_remove+1]+1]
            lose += md[ro[i_remove-1]+1][ro[i_remove]+1]
            lose += md[ro[i_remove]+1][ro[i_remove+1]+1]
    else:
        if i_remove == 1:
            lose += md[ro[i_remove-1]][ro[i_remove]+1]
        else:
            lose += md[ro[i_remove-1]+1][ro[i_remove]+1]
    return round((lose - gain)/1_000,3)

def selectPossible(possibles: List[RoutePossible]):
    selected = None
    value_s = 0
    for possible in possibles:
        if possible.gain > value_s:
            selected = possible
            value_s = possible.gain
    return selected

# r1 é onde o i_insert será inserido
# para inserção do i_insert é necessário verificar onde ele deve ficar 
# depois do deposito
# r2 será onde o i_insert será removido
# dado r1 = [0, 1, 2, 3, 4] e i_insert = 7 (index r2)
# r1 terá 5 possibilidades
# [0, r2[p_insert], 1, 2, 3, 4]
# [0, 1, r2[p_insert], 2, 3, 4]
# [0, 1, 2, r2[p_insert], 3, 4]
# [0, 1, 2, 3, r2[p_insert], 4]
# [0, 1, 2, 3, 4, r2[p_insert]] # custo de remover elemento da r2
def insertBothInRoute(
    md, instance,
    r1, r2, 
    i_insert, selected: int):
    removePack = compensationRemoveInRoute(md, r2, i_insert)
    possibles = []
    select = [selected, selected]
    if constraintCapacityAdd(instance, r1, instance.deliveries[r2[i_insert]]):
        for i in range(1,len(r1)+1):
            poss = {}
            new_route1 = r1.copy()
            new_route1.insert(i, r2[i_insert])
            gain = compensationInsertInRoute(md, r1, r2[i_insert], i)
            new_route2 = [cor for cor in r2 if cor != r2[i_insert]] # remover o r2[p_insert]
            # print("routes")
            # print(new_route1)
            # print(new_route2)
            if gain > 0:
                poss = RoutePossible(new_route1, new_route2, round((gain+removePack),3), select)
                possibles.append(poss)
        possibleInsert = selectPossible(possibles)
    else:
        return None # nao ocupou espaço
    return possibleInsert

# retornar todas as 2 possiveis rotas finais com o valor de perda e de ganho
#   possibles: [{
#       route1: [],
#       route2: [],
#       gain: rotas descartadas - rotas construidas,
#       select: destiny_pack1 (1|2), destiny_pack2 (1|2)
#   }, {...}]
# }
def constructPossiblesSolutions(
    md, instance: CVRPInstance, 
    route1: list, route2: list, 
    p1: int, p2: int):
    possibles = []
    swap = swapPacks(md, instance, route1, route2, p1, p2)
    if swap != None:
        possibles.append(swap)
    possibleRoute1 = insertBothInRoute(md, instance, route1, route2, p2, 1) # p2 -> route1
    if possibleRoute1 != None:
        possibles.append(possibleRoute1)
    possibleRoute2 = insertBothInRoute(md, instance, route2, route1, p1, 2) # p1 -> route2
    if possibleRoute2 != None:
        possibles.append(possibleRoute2)
    return possibles

def twoOptStarModificated(route1, route2, md, instance):
    p1, p2 = 1, 1
    while p1 < len(route1) and p2 < len(route2):
        # print(p1,p2)
        possibles_solutions = constructPossiblesSolutions(
            md, instance, 
            route1, route2, 
            p1, p2)
        best_solution = selectPossible(possibles_solutions)
        if best_solution != None:
            # print(best_solution.gain)
            # print("ANTES")
            # print(route1)
            # print(route2)
            route1, route2  = best_solution.route1.copy(), best_solution.route2.copy()
            if best_solution.select[0] != best_solution.select[1]:
                p1 += 1
                p2 += 1
            else:
                if best_solution.select[0] == 1:
                    p1 += 1
                else:
                    p2 += 1
            # print("DEPOIS")
            # print(route1)
            # print(route2)  
        else:
            p1 += 1
            p2 += 1
              
    return route1, route2
