from collections import deque
from math import ceil

from .classes.exceptions import NoRouterFound
from .classes.types import *
from .computeDistances import *
from .interRoute import *


def routingBatchs(vehiclesPossibles: dict, batch: deque, instance: CVRPInstance, 
    matrix, T, deliveries, decrease):
    """Roteirizando um lote, os deliveries são aqueles já roteirizados que podem ser excluidos"""
    order_batch = orderBatch(batch, instance, vehiclesPossibles, decrease, matrix)
    # percorrer a fila dos pacotes dinamicos
    # print([d.idu for d in order_batch])
    # print(len(order_batch))
    possis = []
    while len(order_batch) > 0:
        poss = [p.idu for p in order_batch]
        # print("TAMANHO DO LOTE: "+str(len(order_batch)))
        # tira o primeiro pacote dinamico do batch
        pack = order_batch.popleft() # Delivery()
        routingPack(vehiclesPossibles, pack, matrix, instance, order_batch, T, deliveries, poss in possis)
        possis.append(poss)
    return order_batch

def orderBatch(batch, instance, vehiclesPossibles, order, md):
    """Se order = 1 é ordem crescente e -1 decrescente"""
    if order != None:
        packetsExist = whoIsOrder(vehiclesPossibles, instance)
        for p in batch:
            packetsExist.append(p)
        orderBatch = buildMetric(instance, batch, packetsExist, order, md)
    else:
        orderBatch = batch
    return orderBatch

def whoIsOrder(vehiclesPossibles, instance):
    deposit = instance.origin
    packets = [deposit]
    for k, v in vehiclesPossibles.items():
        dep = 0
        for id_pack in v[0]:
            if dep == 0:
                dep += 1
            else:
                packets.append(instance.deliveries[id_pack])
    return packets

def buildMetric(instance, batch, packetsExist, order, md):
    distances_pack = {}
    orderBatchList = []
    for p in batch:
        distances_pack[p.idu] = meanDistance(p, packetsExist, md)
    # construir o batch crescente/decrescente
    for i in sorted(distances_pack, key = distances_pack.get, reverse=order):
        orderBatchList.append(instance.deliveries[i])
    orderBatch = deque(orderBatchList)
    return orderBatch

def meanDistance(p, packetsExist, md):
    d = 0
    for atual in packetsExist:
        if(type(atual) is Point):
            d += md[0][p.idu+1]
        else:
            d += md[p.idu+1][atual.idu+1]
    return d/len(packetsExist)

def routingPack(vPoss, packet: Delivery, md, instance, batch, T, deliveries, loop):
    """
    Roteirizando um pacote dinamico (packet)
    """
    attempt = 0
    id_pack = packet.idu
    routes_neig = lookForNeighboringRoutes(packet, deliveries, md, vPoss, T) 
    if loop == False:
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
    if attempt == len(routes_neig) or loop: 
        newRoute, id_route1 = createNewRoute(id_pack, vPoss, 180, deliveries) #ok
        # REAVALIAR A ROTA VIZINHA
        if attempt != 0:
            rneigh = lookForNeighboringRoutes(packet, deliveries, md, vPoss, 1) 
            r1, r2 = bestLocalTwoOptModificated(
                newRoute, vPoss[rneigh[0]][0], md, instance
            )
            # MODIFICAR O VEHICLESPOSSIBLE
            createNewSolution(id_route1, rneigh[0], r1, r2, vPoss)

def reduceVehicle(instance, vPoss, matrix):
    """Reduzir o número de veículos"""
    # calcular o total de cargas no sistema / carga maxima = numero minimo de veiculos
    num_min_vehicles = ceil(sum([d.size for d in instance.deliveries])/180)
    num_vehicles = len(vPoss) # numero de veiculos atual
    print(num_min_vehicles,num_vehicles)
    if num_min_vehicles <= num_vehicles:
        metric = "DENSITY" 
        # metric =  "CAPACITY"
        vehicle_selected, id_route = selectWeakRoute(instance, vPoss, metric, matrix)
        vPoss = destroyVehicle(
            instance, 
            vPoss, 
            vehicle_selected, 
            id_route, 
            matrix)
    return vPoss

def reduceVehiclesDinamic(instance, vPoss, matrix):
    """Reduzir o número de veículos"""
    # calcular o total de cargas no sistema / carga maxima = numero minimo de veiculos
    num_min_vehicles = ceil(sum([d.size for d in instance.deliveries])/180)
    num_vehicles = len(vPoss) # numero de veiculos atual
    print(num_min_vehicles,num_vehicles)
    N = num_vehicles-num_min_vehicles-1
    if num_min_vehicles <= num_vehicles:
        metric = "DENSITY" 
        # metric =  "CAPACITY"
        vehicles_selecteds, ids_routes = selectWeakestRoutes(instance, vPoss, metric, matrix, N)
        vPoss = destroyVehicles(
            instance, 
            vPoss, 
            vehicles_selecteds, 
            ids_routes, 
            matrix)
    return vPoss


def destroyVehicle(instance: CVRPInstance, vPoss, route_selected, id_route, matrix):
    """A ideia dessa função é diminuir o número de rotas"""
    # remover o vehicle selecionado e 
    print(vPoss[id_route])
    del vPoss[id_route]
    # rotear os pacotes livres
    batch = buildBatchRoute(route_selected, instance)
    dinamics = []
    routingBatchs(vPoss,deque(batch),instance,matrix,20,dinamics,None)
    print(vPoss)
    return vPoss

def destroyVehicles(instance: CVRPInstance, vPoss, routes_selecteds, ids_routes, matrix):
    """A ideia dessa função é diminuir o número de rotas"""
    # remover o vehicle selecionado e 
    for id_route in ids_routes:
        # print(vPoss[id_route])
        del vPoss[id_route]
    # rotear os pacotes livres
    batch, deliveries_exists = buildBatchRoutes(routes_selecteds, instance)
    # print([d.idu for d in batch])
    routingBatchs(vPoss,deque(batch),instance,matrix,30,deliveries_exists,None)
    return vPoss

def buildBatchRoute(route_select, instance):
    dep = 0
    route = []
    for r in route_select:
        if dep == 0:
            dep += 1
        else:
            route.append(instance.deliveries[r])
    return route

def buildBatchRoutes(routes_selects, instance):
    route = []
    deliveries = []
    for route_select in routes_selects:
        dep = 0
        for r in route_select:
            if dep == 0:
                dep += 1
            else:
                route.append(instance.deliveries[r])
    for d in instance.deliveries:
        if d not in route:
            deliveries.append(d.idu)
    # print(len(deliveries), len(route))
    return route, deliveries

def selectWeakRoute(instance, vPoss, metric, md):
    """Deve retornar a rota do vehicle selecionado e o id para ser removido"""
    route_select = []
    id_route = 0
    if metric == "DENSITY":
        density_distance_max = 0
        for k, v in vPoss.items():
            density_distance = calculateDensityDistance(v[0], md)
            if density_distance_max < density_distance:
                route_select = v[0]
                id_route = k
    elif metric == "CAPACITY":
        cap_min = 200
        for k, v in vPoss.items():
            capacity = sum([instance.deliveries[d].size for d in v[0]])
            if cap_min > capacity:
                cap_min = capacity
                route_select = v[0]
                id_route = k    
    return route_select, id_route

def selectWeakestRoutes(instance, vPoss, metric, md, MIN_ROUTES):
    """Deve retornar a rota do vehicle selecionado e o id para ser removido"""
    routes_selects = []
    decrease = False
    ids_routes = []
    routes = {}
    cont = 0
    if metric == "DENSITY":
        decrease = True
        for k, v in vPoss.items():
            print(v)
            density_distance = calculateDensityDistance(v, md)
            routes[k] = density_distance
    elif metric == "CAPACITY":
        decrease = False
        for k, v in vPoss.items():
            capacity = sum([instance.deliveries[d].size for d in v[0]])
            routes[k] = capacity
    for i in sorted(routes, key = routes.get, reverse=decrease):
        if cont < MIN_ROUTES:
            cont += 1
            ids_routes.append(i)
            routes_selects.append(vPoss[i])  
    return routes_selects, ids_routes

def calculateDensityDistance(route, md):
    """Calcula a densidade de distancia por pacote"""
    npackets = len(route)
    distance = 0
    for i in range(1,len(route)):
        if i == 1:
            distance = md[0][route[i]+1]
        else:
            distance += md[route[i-1]+1][route[i]+1]
    return float(distance/npackets)

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
    # print("Pacote " +str(worst_pack_id) + " removido.")
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
        # print("pacote " +str(id_packet)+ " encontrou na rota")
        deliveries.append(id_packet)
        # print(vPoss[rSelect][0])
        vPoss[rSelect][0] = route_fake
    else:
        worst_pack_id = selectWorstPacket(vPoss[rSelect][0], md)
        route_worstpack = createRouteNoWorst(worst_pack_id, vPoss[rSelect][0])
        route_newpacket = insertNewPacket(id_packet, route_worstpack, md)
        # print("COMPARE =>")
        # print(route_newpacket)
        # print(vPoss[rSelect][0])
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
    # print("Packet id = "+str(id_packet) + " será inserido na rota")
    # print(route)
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
    # print(packet.idu)
    # Dicionario com chave: id delivery, valor: distancia do pacote atual ate outro pacote
    for i in deliveries:
      neighs[i] = md[packet.idu+1][i+1]
    # Aqui temos um vetor ordenado de todos os pacotes proximos
    if len(deliveries) != 0:
        for id in sorted(neighs, key = neighs.get):
            packs_neigs.append(id)
        auxT = 0
        for d in packs_neigs:
            if auxT < T:
                for k, v in vPoss.items():
                    if d in v:
                        if k not in routes_neigs:
                            routes_neigs.append(k)
                        auxT += 1
    return routes_neigs

def createNewRoute(packet_id, vehiclesPossibles, newCap, deliveries):
    """Criar uma nova rota do deposito até o packet"""
    # Duas opções -> Buscar 1 veículo disponivel ou Buscar 1 veículo padrão
    # Veículo padrão
    try:
        newVehicle = max(vehiclesPossibles) + 1
    except ValueError:
        newVehicle = 1
    vehiclesPossibles[newVehicle] = [[0, packet_id], newCap]
    deliveries.append(packet_id)
    # print("Nova rota criada")
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
    # print(route)
    for id_pack in route:
        cap += instance.deliveries[id_pack].size
    return cap <= capacityMax