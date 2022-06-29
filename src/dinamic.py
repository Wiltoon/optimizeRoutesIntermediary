from collections import deque

from .classes.exceptions import NoRouterFound
from .classes.types import *
from .computeDistances import *
from .interRoute import *


def routingBatchs(vehiclesPossibles: dict, batch: deque, instance: CVRPInstance, 
    matrix, T, deliveries):
    """Roteirizando um lote"""
    # percorrer a fila dos pacotes dinamicos
    while len(batch) > 0:
        # tira o primeiro pacote dinamico do batch
        pack = batch.popleft() 
        print(pack)
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
            insertionPackInRoute(
                instance, id_pack, vPoss, rSelect, batch, md, deliveries
            ) #OK?
            break
        except NoRouterFound:
            attempt += 1
    # acabou o número de rotas vizinhas do pack dinamico e não foi alocado
    # print(id_pack, attempt)
    if attempt == len(routes_neig): 
        newRoute, id_route1 = createNewRoute(id_pack, vPoss, 180, deliveries) #ok
        # REAVALIAR A ROTA VIZINHA
        if attempt != 0:
            rneigh = lookForNeighboringRoutes(packet, deliveries, md, vPoss, 1) 
            r1, r2 = bestLocalTwoOptModificated(
                newRoute, vPoss[rneigh[0]][0], md, instance
            )
            # MODIFICAR O VEHICLESPOSSIBLE
            createNewSolution(id_route1, rneigh[0], r1, r2, vPoss)


def selectWorstPacket(route, md):
    """
    Selecionar o id do pior pacote da rota CONSIDERE O DEPOSITO
    """
    worstScore = 0
    id_worst = -1
    if len(route) > 0:
        for i in range(1,len(route)):
            score = availablePack(route, i, md)
            if worstScore < score:
                id_worst = route[i]
    return id_worst

def availablePack(route, i, md):
    """
    Avaliar o score de um pacote dentro de uma rota
    """
    if i >= 1: # a rota tem q ter pelo menos um pacote
        id_prev = route[i-1]+1
        id_act = route[i]+1
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
        return route.copy()
    return [id for id in route if id != id_pack]


def kickOutWorst(instance, route, worst_pack_id, batch_d, deliveries):
    """
    Acrescenta o pior pacote na lista dos não visitados
    e retira o pior pacote da rota original
    """
    print("Pacote " +str(worst_pack_id) + " removido.")
    batch_d.append(instance.deliveries[worst_pack_id])
    route = createRouteNoWorst(worst_pack_id, route)  
    deliveries.remove(worst_pack_id)
    return route

def insertionPackInRoute(instance: CVRPInstance, id_packet: int, vPoss,
    rSelect, batch_d, md, deliveries):
    """
    Tenta inserir um pacote dinamico na rota, 
    se falhar tenta expulsar o pior pacote da rota selecionada
    """
    route_fake = insertNewPacket(id_packet, vPoss[rSelect][0], md) #ok
    if capacityRoute(route_fake, instance, vPoss[rSelect][1]): #ok
        print("pacote " +str(id_packet)+ " encontrou na rota")
        deliveries.append(id_packet)
        print(vPoss[rSelect][0])
        vPoss[rSelect][0] = route_fake
    else:
        worst_pack_id = selectWorstPacket(vPoss[rSelect][0], md)
        route_worstpack = createRouteNoWorst(worst_pack_id, vPoss[rSelect][0])
        route_newpacket = insertNewPacket(id_packet, route_worstpack, md)
        print("COMPARE =>")
        print(route_newpacket)
        print(vPoss[rSelect][0])
        if compareRoutes(route_newpacket, vPoss[rSelect][0], md):
            vPoss[rSelect][0] = kickOutWorst(
                instance, vPoss[rSelect][0], worst_pack_id, batch_d, deliveries
            )
            # print(vPoss[rSelect][0])
            insertionPackInRoute(instance, id_packet, vPoss, rSelect, batch_d, md, deliveries)
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
    route_supos = route.copy()
    print("Packet id = "+str(id_packet) + " será inserido na rota")
    print(route)
    p_insertion = []
    for i in range(1,len(route)+1):
        route_aux = [el for el in route]
        route_aux.insert(i, id_packet)
        p_insertion.append(route_aux)
    scores = []
    # print(p_insertion)
    for possible in p_insertion:
        score = calculateDiferenceDistanceRoute(matrix_distance, route, possible)
        scores.append(score)
    # print("Minimo")
    # print(p_insertion[scores.index(min(scores, key = float))])
    route_supos = p_insertion[scores.index(min(scores, key = float))] 
    # print(route)
    # lista de pacotes arranjado da melhor forma
    return route_supos    

def lookForNeighboringRoutes(packet: Delivery, deliveries, md, vPoss: dict, T: int):
    """Procura pelas rotas vizinhas"""
    routes_neigs = []
    neighs = {}
    packs_neigs = []
    # print("LOOKING =>")
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
                for k, v in vPoss.items():
                    if d in v[0]:
                        if k not in routes_neigs:
                            routes_neigs.append(k)
                        auxT += 1
    return routes_neigs

def createNewRoute(packet_id, vehiclesPossibles, newCap, deliveries):
    """Criar uma nova rota do deposito até o packet"""
    # Duas opções -> Buscar 1 veículo disponivel ou Buscar 1 veículo padrão
    # Veículo padrão
    newVehicle = len(vehiclesPossibles) + 1
    vehiclesPossibles[newVehicle] = [[0, packet_id], newCap]
    deliveries.append(packet_id)
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
    vehiclesPossibles[id_route1] = [r1,vehiclesPossibles[id_route1][1]]
    vehiclesPossibles[id_route2] = [r2,vehiclesPossibles[id_route2][1]]

def capacityRoute(route, instance: CVRPInstance, capacityMax) -> bool:
    """Retorna verdadeiro se a capacidade da rota foi respeitada"""
    cap = 0
    print(route)
    for id_pack in route:
        cap += instance.deliveries[id_pack].size
    return cap <= capacityMax