from xmlrpc.client import Boolean
from classes.exceptions import NoRouterFound
from computeDistances import calculateDistanceRoute
from interRoute import twoOptStarModificated


def collectBatchs(batch):
    # percorrer a fila dos pacotes dinamicos
    # tira o primeiro pacote dinamico do batch
    # roteiriza o pacote dinamico
    return batch

def routingPack(solution_initial, packet, matrix_d, instance, batch):
    #devolve lista das rotas vizinhas do pack dinamico
    attempt = 0
    routes_neig = lookForNeighboringRoutes(packet, solution_initial, matrix_d) 
    for rSelect in routes_neig:
        try:
            insertionPackInRoute(packet, rSelect, batch)
            break
        except NoRouterFound:
            attempt += 1
    if attempt == len(routes_neig): 
        # sem rotas vizinhas do pack dinamico
        newRoute = createNewRoute(packet, solution_initial)
        r1, r2 = bestLocalTwoOptModificated(
            newRoute, routes_neig[0], matrix_d, instance
        )
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
        
def lookForNeighboringRoutes(
    packet, 
    instance, 
    md,
    vehiclesPossibles, 
    T):
    routes_neigs = []
    neighs = {}
    packs_neigs = []

    # Dicionario com chave: id delivery, valor: distancia do pacote atual ate outro pacote
    for i in range(1,len(instance.deliveries)+1):
      neighs[i] = md[packet.idu+1][i]
    # Aqui temos um vetor ordenado de todos os pacotes proximos
    for id in sorted(neighs, key = neighs.get):
      packs_neigs.append(id)
    auxT = 0
    for d in packs_neigs:
      if auxT < T:
        for k, v in vehiclesPossibles.items():
            if d in v:
                if k not in routes_neigs:
                    routes_neigs.append(k)
                auxT += 1
    return routes_neigs

def createNewRoute(packet, solution_initial):
    # criar uma nova rota do deposito até o packet
    pass

def bestLocalTwoOptModificated(route1, route2, md):
    """Ajusta as melhores posições para as rotas"""
    bestScore = calculateDistanceRoute(route1, route2, md)+1
    score = bestScore-1
    while score < bestScore:
        bestScore = score
        score = twoOptStarModificated(route1, route2, md) 
    return route1, route2

def createNewSolution():
    """a nova solução deve compor o vehiclePossible"""
    pass

def capacityRoute(route: CVRPSolutionVehicle) -> bool:
    """Retorna verdadeiro se a capacidade da rota foi respeitada"""
    return route.occupation() <= route.capacity