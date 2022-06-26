from classes.exceptions import NoRouterFound
from computeDistances import calculateDistanceRoute


def collectBatchs(batch):
    # percorrer a fila dos pacotes dinamicos
    # tira o primeiro pacote dinamico do batch
    # roteiriza o pacote dinamico

def routingPack(solution_initial, packet, matrix_d, instance, batch):
    #devolve lista das rotas vizinhas do pack dinamico
    attempt = 0
    routes_neig = lookForNeighboringRoutes(packet, solution_initial) 
    for rSelect in routes_neig:
        try:
            insertionPackInRoute(packet, rSelect, batch)
            break
        except NoRouterFound:
            attempt += 1
    if attempt == len(routes_neig): # sem rotas vizinhas do pack dinamico
        newRoute = createNewRoute(packet, solution_initial)
        r1, r2 = twoOptStarModificated(newRoute, routes_neig[0], matrix_d, instance)
        newRoute = r1.copy() # modificar a nova rota
        routes_neig[0] = r2.copy() # modificar a rota vizinha
        createNewSolution(newRoute, solution_initial)
    
def insertionPackInRoute(packet, route, batch_d, md):
    route_fake = insertNewPacket(packet, route, md)
    if capacityRoute(route_fake):
        # pacote encontrou a rota
        print("WORK!")
    else:
        worst_pack = selectWorstPacket(route)
        route_newpacket = createRouteNoWorst(worst_pack, route)
        route_worstpack = route.copy()
        select = compareRoutes(route_newpacket, route_worstpack)
        if select == 1:
            kickOutWorst(route, worst_pack, batch_d)
            insertionPackInRoute(packet, route, batch_d, md)
        elif select == 2:
            raise NoRouterFound("Próxima rota!")
        else:
            raise Exception("Not implemented!!!")
def insertNewPacket(packet, route, matrix_distance):
    p_insertion = []
    # print("Route list = ")
    # print(route)
    for i in range(1,len(route)+1):
        route_aux = [el for el in route]
        route_aux.insert(i, packet-1)
        p_insertion.append(route_aux)
    scores = []
    # print(p_insertion)
    for possible in p_insertion:
        score = calculateDistanceRoute(matrix_distance, route, possible)
        scores.append(score)
    # print("Minimo")
    # print(p_insertion[scores.index(min(scores, key = float))])
    route = p_insertion[scores.index(min(scores, key = float))] 
    # lista de pacotes arranjado da melhor forma
    return route
        


            
            