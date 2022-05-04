# Here we have 2opt* with aim of swap 1 route's pack for another route's pack 
from .classes.types import Delivery


def compensation(md, r1, r2, i, j):
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
    gain1, lose1 = compensation(md, route1, route2, p1, p2)
    gain2, lose2 = compensation(md, route2, route1, p2, p1)
    loseSwap = lose1 + lose2
    gainSwap = gain1 + gain2
    return gainSwap, loseSwap

def twoOptStar(route1, route2, md, instance):
    # print(route1)
    # print(route2)
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
