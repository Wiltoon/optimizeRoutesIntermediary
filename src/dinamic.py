from xmlrpc.client import Boolean
from collections import deque

from matplotlib.style import available
from classes.exceptions import NoRouterFound
from classes.types import *
from computeDistances import *
from interRoute import *


def routingBatchs(vehiclesPossibles: dict, batch: deque, instance: CVRPInstance, 
    matrix, T, deliveries):
    """Roteirizando um lote"""
    # percorrer a fila dos pacotes dinamicos
    while len(batch) > 0:
        id_pack = batch.popleft() 
        # tira o primeiro pacote dinamico do batch
        pack = instance.deliveries[id_pack] # EXISTE O ID = 0 para pacotes
        # roteiriza o pacote dinamico
        routingPack(vehiclesPossibles, pack, matrix, instance, batch, T, deliveries)
    return batch
    
def routingPack(vPoss, packet: Delivery, md, instance, batch, T, deliveries):
    """
    Roteirizando um pacote dinamico
    """
    attempt = 0
    id_pack = packet.idu
    routes_neig = lookForNeighboringRoutes(packet, deliveries, md, vPoss, T) 
    for rSelect in routes_neig:
        try:
            routeSelect = vPoss[rSelect][0]
            capRoute = vPoss[rSelect][1]
            insertionPackInRoute(id_pack, routeSelect, capRoute, batch, md, deliveries) #OK?
            break
        except NoRouterFound:
            attempt += 1
    # acabou o número de rotas vizinhas do pack dinamico e não foi alocado
    if attempt == len(routes_neig): 
        newRoute, id_route1 = createNewRoute(id_pack, vPoss) #ok
        # REAVALIAR A ROTA VIZINHA
        rneigh = lookForNeighboringRoutes(packet, deliveries, md, vPoss, 1) 
        r1, r2 = bestLocalTwoOptModificated(
            newRoute, vPoss[rneigh[0]][0], md, instance
        )
        # MODIFICAR O VEHICLESPOSSIBLE
        createNewSolution(id_route1, rneigh[0], r1, r2, vPoss)

def selectWorstPacket(route, instance: CVRPInstance):
    """
    Selecionar o id do pior pacote da rota CONSIDERE O DEPOSITO
    """
    worstScore = 0
    id_worst = -1
    if len(route) > 0:
        for i in (1,len(route)):
            score = availablePack(route, i, instance)
            if worstScore < score:
                id_worst = route[i]
    return id_worst
def availablePack(route, i, md):
    """
    Avaliar o score de um pacote dentro de uma rota
    """
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
    """
    Cria uma lista sem o id_pack da rota
    """
    if id_pack == -1:
        return route
    return [id for id in route if id != id_pack]
def kickOutWorst(route, worst_pack_id, batch_d, deliveries):
    """
    Acrescenta o pior pacote na lista dos não visitados
    e retira o pior pacote da rota original
    """
    print("Pacote " +str(worst_pack_id) + " removido.")
    batch_d.append(worst_pack_id)
    route = createRouteNoWorst(worst_pack_id, route)  
    deliveries.remove(worst_pack_id)

def insertionPackInRoute(instance: CVRPInstance, id_packet: int, route,
    capRoute, batch_d, md, deliveries):
    """
    Tenta inserir um pacote dinamico na rota, 
    se falhar tenta expulsar o pior pacote da rota selecionada
    """
    route_fake = insertNewPacket(id_packet, route, md) #ok
    if capacityRoute(route_fake, instance, capRoute): #ok
        print("pacote " +str(id_packet)+ " encontrou a rota")
        route = route_fake.copy()
        deliveries.append(id_packet)
    else:
        worst_pack_id = selectWorstPacket(route)
        route_worstpack = createRouteNoWorst(worst_pack_id, route)
        route_newpacket = insertNewPacket(id_packet, route_worstpack, md)
        if compareRoutes(route_newpacket, route, md):
            kickOutWorst(route, worst_pack_id, batch_d)
            insertionPackInRoute(id_packet, route, capRoute, batch_d, md)
        else:
            raise NoRouterFound("Próxima rota!")
            
def compareRoutes(route1, route2, md):
    """
    Compara duas rotas e devolve 
    Verdadeiro se a primeira for melhor e 
    False se a segunda for melhor
    """
    score1 = computeDistanceRoute(route1, md)
    score2 = computeDistanceRoute(route2, md)
    if score1 < score2:
        return True
    else:
        return False

def insertNewPacket(id_packet, route, matrix_distance):
    """Insere o pacote dinamico na melhor posição da rota"""
    # Verificar se esta adicionando o deposito no inicio 
    print("Packet id ="+str(id_packet) + " será inserido na rota")
    print(route)
    p_insertion = []
    for i in range(1,len(route)+1):
        route_aux = [el for el in route]
        route_aux.insert(i, id_packet+1)
        p_insertion.append(route_aux)
    scores = []
    # print(p_insertion)
    for possible in p_insertion:
        score = calculateDiferenceDistanceRoute(matrix_distance, route, possible)
        scores.append(score)
    # print("Minimo")
    # print(p_insertion[scores.index(min(scores, key = float))])
    route = p_insertion[scores.index(min(scores, key = float))] 
    # lista de pacotes arranjado da melhor forma
    return route    

def lookForNeighboringRoutes(
    packet: Delivery, 
    deliveries, 
    md,
    vehiclesPossibles: dict, # modificado
    T: int):
    """Procura pelas rotas vizinhas"""
    routes_neigs = []
    neighs = {}
    packs_neigs = []
    
    # Dicionario com chave: id delivery, valor: distancia do pacote atual ate outro pacote
    for i in deliveries:
      neighs[i] = md[packet.idu+1][i]
    # Aqui temos um vetor ordenado de todos os pacotes proximos
    if len(deliveries) != 0:
        for id in sorted(neighs, key = neighs.get):
            packs_neigs.append(id)
        auxT = 0
        for d in packs_neigs:
            if auxT < T:
                for k, v in vehiclesPossibles.items():
                    if d in v[0]:
                        if k not in routes_neigs:
                            routes_neigs.append(k)
                        auxT += 1
    return routes_neigs

def createNewRoute(packet_id, vehiclesPossibles, newCap):
    """Criar uma nova rota do deposito até o packet"""
    # Duas opções -> Buscar 1 veículo disponivel ou Buscar 1 veículo padrão
    # Veículo padrão
    newVehicle = len(vehiclesPossibles) + 1
    vehiclesPossibles[newVehicle] = ([0, packet_id], newCap)
    print("Nova rota criada")
    return vehiclesPossibles[newVehicle][0], newVehicle

def bestLocalTwoOptModificated(route1, route2, md, instance):
    """Ajusta as melhores posições para as rotas"""
    routes = [route1, route2]
    bestScore = calculateDistanceRoutes(routes, md)+1
    score = bestScore-1
    while score < bestScore:
        bestScore = score
        score = twoOptStarModificatedScore(route1, route2, md, instance) 
    return route1, route2

def createNewSolution(id_route1, id_route2, r1, r2, vehiclesPossibles):
    """a nova solução deve compor o vehiclePossible"""
    vehiclesPossibles[id_route1] = (r1,vehiclesPossibles[id_route1][1])
    vehiclesPossibles[id_route2] = (r2,vehiclesPossibles[id_route2][1])

def capacityRoute(route, instance: CVRPInstance, capacityMax) -> bool:
    """Retorna verdadeiro se a capacidade da rota foi respeitada"""
    for id_pack in route:
        cap += instance.deliveries[id_pack].size
    return cap <= capacityMax