from xmlrpc.client import Boolean

from matplotlib.style import available
from classes.exceptions import NoRouterFound
from classes.types import *
from computeDistances import calculateDistanceRoute
from interRoute import twoOptStarModificated


def collectBatchs(batch):
    # percorrer a fila dos pacotes dinamicos
    # tira o primeiro pacote dinamico do batch
    # roteiriza o pacote dinamico
    return batch

def routingPack(
    vehiclesPossibles, 
    packet: Delivery, 
    matrix_d, 
    instance, 
    batch, 
    T):
    """Roteirizando um pacote dinamico"""
    #devolve lista das rotas vizinhas do pack dinamico
    attempt = 0
    id_pack = packet.idu
    routes_neig = lookForNeighboringRoutes(
        packet,
        instance,
        matrix_d,
        vehiclesPossibles,
        T
    ) 
    for rSelect in routes_neig:
        try:
            insertionPackInRoute(id_pack, rSelect, batch, matrix_d) #OK?
            break
        except NoRouterFound:
            attempt += 1
    if attempt == len(routes_neig): 
        # sem rotas vizinhas do pack dinamico
        newRoute = createNewRoute(id_pack, vehiclesPossibles)
        r1, r2 = bestLocalTwoOptModificated(
            newRoute, routes_neig[0], matrix_d, instance
        )
        newRoute = r1.copy() # modificar a nova rota
        routes_neig[0] = r2.copy() # modificar a rota vizinha
        createNewSolution(newRoute, solution_initial)
    
def selectWorstPacket(route, instance: CVRPInstance):
    """Selecionar o id do pior pacote da rota CONSIDERE O DEPOSITO"""
    worstScore = 0
    id_worst = -1
    for i in (1,len(route)):
        score = availablePack(route, i, instance)
        if worstScore < score:
            id_worst = route[i]
    return id_worst

def availablePack(route, i, md):
    """Avaliar o score de um pacote dentro de uma rota"""
    if i >= 1: # a rota tem q ter pelo menos um pacote
        id_prev = route[i-1]
        id_act = route[i]
        if i == (len(route)-1): # ultimo elemento
            # id do prox pack = route[i-1] | route[i-1]+1 ?
            return md[id_prev][id_act]
        else:
            id_next = route[i+1]
            return md[id_prev][id_act] + md[id_act][id_next] - md[id_prev][id_next]
    else:
        return 0 

def createRouteNoWorst(id_pack, route):
    """Cria uma lista sem o id_pack da rota"""
    return ([id for id in route if id != id_pack])

def kickOutWorst(route, worst_pack_id, batch_d):
    """Acrescenta o pior pacote na lista dos não visitados
    e retira o pior pacote da rota original"""
    batch_d.append(worst_pack_id)
    route = createRouteNoWorst(worst_pack_id, route)
    
def insertionPackInRoute(instance, packet, route, batch_d, md):
    """Tenta inserir um pacote dinamico na rota, se falhar tenta expulsar o pior pacote da rota selecionada"""
    route_fake = insertNewPacket(packet, route, md) #ok
    if capacityRoute(route_fake, instance, capacityMax=180): #ok
        # pacote encontrou a rota
        route = route_fake.copy()
    else:
        worst_pack_id = selectWorstPacket(route)
        route_worstpack = createRouteNoWorst(worst_pack_id, route)
        route_newpacket = insertNewPacket(packet, route_worstpack, md)
        select = compareRoutes(route_newpacket, route, md)
        if select == 1:
            kickOutWorst(route, worst_pack_id, batch_d)
            insertionPackInRoute(packet, route, batch_d, md)
        elif select == 2:
            raise NoRouterFound("Próxima rota!")
        else:
            raise Exception("Not implemented!!!")

def compareRoutes(route1, route2, md):
    """Compara duas rotas e devolve 
    1 se a primeira for melhor e 
    2 se a segunda for melhor"""
    score1 = calculateDistanceRoute(route1, md)
    score2 = calculateDistanceRoute(route2, md)
    if score1 < score2:
        return 1
    else:
        return 2

def insertNewPacket(packet, route, matrix_distance):
    """Insere o pacote dinamico na melhor posição da rota"""
    # Verificar se esta adicionando o deposito no inicio 
    print("Packet id ="+str(packet) + " será inserido na rota")
    print(route)
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
    """Procura pelas rotas vizinhas"""
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
    """Criar uma nova rota do deposito até o packet"""
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

def capacityRoute(route, instance: CVRPInstance, capacityMax) -> bool:
    """Retorna verdadeiro se a capacidade da rota foi respeitada"""
    for id_pack in route:
        cap += instance.deliveries[id_pack].size
    return cap <= capacityMax