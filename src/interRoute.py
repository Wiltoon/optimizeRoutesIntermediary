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
    total =0 
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
    return gainSwap, loseSwap

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
        gain = loseSwap - gainSwap
        possibleSwap = RoutePossible(
            new_route1,
            new_route2,
            gain,
            select)
    else:
        return None
    return possibleSwap

def compensationInsertInRoute(md, instance, r1, r2, p_insert):
    # pacote da posição p_insert do r2 está indo para o r1
    gainDistanceTotal = 0
    return gainDistanceTotal

def insertBothInRoute(
    md, instance, 
    r1, r2, 
    p_insert, selected: int):
    # r1 é onde o p_insert será inserido
    # para inserção do p_insert é necessário verificar onde ele deve ficar 
    # depois do deposito
    # r2 será onde o p_insert será removido
    # dado r1 = [0, 1, 2, 3, 4] e p_insert = 7 (index r2)
    # r1 terá 5 possibilidades
    # [0, r2[p_insert], 1, 2, 3, 4]
    # [0, 1, r2[p_insert], 2, 3, 4]
    # [0, 1, 2, r2[p_insert], 3, 4]
    # [0, 1, 2, 3, r2[p_insert], 4]
    # [0, 1, 2, 3, 4, r2[p_insert]]
    lose = 4# custo de remover elemento da r2
    possibles = []
    gains = []
    for i in range(1,len(r1)+1):
        new_route1 = r1.insert(i, r2[p_insert])
        gain = compensationInsertInRoute(md, instance, r1, r2, p_insert)
        possibles.append()
    select = [selected, selected]
    possibleInsert = RoutePossible()
    return possibleInsert

def constructPossiblesSolutions(
    md, instance: CVRPInstance, 
    route1: list, route2: list, 
    p1: int, p2: int):
    # retornar todas as 2 possiveis rotas finais com o valor de perda e de ganho
    #   possibles: [{
    #       route1: [],
    #       route2: [],
    #       gain: rotas descartadas - rotas construidas,
    #       select: destiny_pack1 (1|2), destiny_pack2 (1|2)
    #   }, {...}]
    # }
    possibles = []
    swap = swapPacks(md, instance, route1, route2, p1, p2)
    if swap != None:
        possibles.append(swap)
    
    possible = insertBothInRoute1()
    possible = insertBothInRoute2()
    return possibles

def selectBestSolutions(possibles):
    return possibles[0]

def twoOptStarModificated(route1, route2, md, instance):
    # print(route1)
    # print(route2)
    p1, p2 = 0, 0
    while p1 < len(route1):
        while p2 < len(route2):
            possibles_solutions = constructPossiblesSolutions(md, route1, route2, p1, p2)
            best_solution = selectBestSolutions(possibles_solutions)
            route1, route2 = best_solution['route1'], best_solution['route2']
            if best_solution['select'][0] != best_solution['select'][1]:
                p1 += 1
                p2 += 1
            else:
                if best_solution['select'][0] == 1:
                    p1 += 1
                else:
                    p2 += 1

    for p1 in range(1,len(route1)):
        for p2 in range(1,len(route2)):
            if swapPossible(instance, route1, route2, p1, p2):
                gainSwap, loseSwap = computeCompensationSwap(md, route1, route2, p1, p2)
                if loseSwap > gainSwap:
                    new_route1 = [route1[i] for i in range(len(route1)) if i != p1]
                    new_route1.insert(p1, route2[p2])
                    new_route2 = [route2[j] for j in range(len(route2)) if j != p2]
                    new_route2.insert(p2, route1[p1])
                    route1 = new_route1.copy()
                    route2 = new_route2.copy()
                
    return route1, route2
