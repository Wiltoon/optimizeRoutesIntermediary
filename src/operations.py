from .classes.types import *
from .computeDistances import *
# Essa função deve decidir em qual rota vizinha o pacote (id_pack) deve ser inserido
# e modificar o vehicles Possibles de como ficará as rotas
def insertionPackInNeighborhood(
    vehiclesPossibles, 
    routes_neighs, 
    id_pack: int,
    id_old_route: int,
    matrix_distance
    ):
  best_values = []
  best_routes = []
  neighbors = list(dict.fromkeys(routes_neighs)) # neighbors retorna uma lista de rotas vizinhas sem repetição de rotas
  for id_route in neighbors:
    # print(id_route)
    # print("Pack = "+ str(id_pack))
    route, min_value = insertPacketInRoute(
      id_pack, 
      vehiclesPossibles[id_route], 
      matrix_distance
    )
    best_values.append(min_value) # calcula a distancia da melhor posição para o pacote ficar na rota
    best_routes.append(route)     # lista das rotas vizinhas construidas com o pacote
  if len(best_values) != 0:
    id_b = best_values.index(min(best_values, key = float))
    id_best_route = neighbors[id_b]
    route_create = best_routes[id_b]
    create_new_solution(
      new_route = route_create,
      vehiclesPossibles = vehiclesPossibles, # modificado
      id_pack_modificated = id_pack, 
      id_old_route = id_old_route,
      id_new_route = id_best_route
      ) # teoricamente o vehiclesPossibles precisa estar com a resposta final

def createVehiclesPossibles(solution: CVRPSolution):
  #enumere as rotas da solution
  #enumere os pacotes 
  #chave id_route 
  #valor [id_packs]
  vehiclesPossible = {}
  for v in range(len(solution.vehicles)):
    vehiclesPossible[v] = []
    for d in solution.vehicles[v].deliveries:
      vehiclesPossible[v].append(d.idu)

  for k, v in vehiclesPossible.items():
    if len(vehiclesPossible[k]) >= 1:
      vehiclesPossible[k].insert(0, 0)

  return vehiclesPossible

def createVehiclesPossibles(solution: CVRPSolutionKpprrf):
  #enumere as rotas da solution
  #enumere os pacotes 
  #chave id_route 
  #valor [id_packs]
  vehiclesPossible = {}
  for v in range(len(solution.vehicles)):
    vehiclesPossible[v] = []
    for d in solution.vehicles[v].deliveries:
      vehiclesPossible[v].append(d.idu)

  for k, v in vehiclesPossible.items():
    if len(vehiclesPossible[k]) >= 1:
      vehiclesPossible[k].insert(0, 0)

  return vehiclesPossible

# dado o dicionario transformar ele em resposta cvrp solution
def create_new_solution(
  new_route,
  vehiclesPossibles, # modificado
  id_pack_modificated, 
  id_old_route,
  id_new_route
  ):
  # print("id rota = " + str(id_old_route))
  # print("id nova rota = " + str(id_new_route))
  # print("id pack mod = "+str(id_pack_modificated))
  vehiclesPossibles[id_old_route].remove(id_pack_modificated-1)
  if len(vehiclesPossibles[id_old_route]) <= 1:
    vehiclesPossibles.pop(id_old_route, 404)
  vehiclesPossibles[id_new_route] = new_route

  # print("============ MODIFICATED ==========")
  # print(vehiclesPossibles)
  # print("-----------------------------------")


# Essa função deve avaliar determinado pacote em uma rota e qual o melhor resultado
def insertPacketInRoute(
    id_pack, # 153
    route_select, # saber qual o id dos packs dessa rota 
    matrix_distance):
  p_insertion = []
  # print("Route list = ")
  # print(route_select)
  for i in range(1,len(route_select)+1):
    route_aux = [el for el in route_select]
    route_aux.insert(i, id_pack-1)
    p_insertion.append(route_aux)
  scores = []
  # print(p_insertion)
  for possible in p_insertion:
    score = calculateDistanceRoute(matrix_distance, route_select, possible)
    scores.append(score)
  # print("Minimo")
  # print(p_insertion[scores.index(min(scores, key = float))])
  route = p_insertion[scores.index(min(scores, key = float))] # lista de pacotes arranjado da melhor forma
  return route, min(scores, key = float)

#retornar a rota do veículo de menor uso e seu id
def selectVehicleWeak(instance, solution):
  MAX_ = instance.vehicle_capacity
  minVehicles = sum([d.size for d in instance.deliveries])/MAX_
  sumVehicles = len(solution.vehicles)
  vehicles_ordened = {}
  if sumVehicles <= minVehicles:
    return None, -1
  for v in range(len(solution.vehicles)):
    vehicles_ordened[v] = sum([d.size for d in solution.vehicles[v].deliveries])
  for i in sorted(vehicles_ordened, key = vehicles_ordened.get):
    sizeUsed = vehicles_ordened[i]
    if sizeUsed > 0.5*MAX_:
      return None, -1
    else:
      weak = i
      vehicleWeak = solution.vehicles[weak].deliveries
      return vehicleWeak, weak

# Retorna um vetor com os indices dos veículos ordenados dado uma lista de veículos
def sortedVehiclesPerChargeUsed(vehicles):
  cargas = {}
  vehicles_ordened = []
  for i in range(len(vehicles)):
    carga = [d.size for d in vehicles[i].deliveries]
    cargas[i] = sum(carga)
  for i in sorted(cargas, key = cargas.get):
    vehicles_ordened.append(i)
  return vehicles_ordened

def solutionJson(
  instance: CVRPInstance, 
  vehiclesPossibles
  )-> CVRPSolution:
  name = instance.name
  vehicles = []
  for k, v in vehiclesPossibles.items():
    vehicle = []
    dep = 0
    for id_pack in v:
      if dep == 0:
        dep += 1
        continue
      else:
        point = Point(
          lng=instance.deliveries[id_pack].point.lng, 
          lat=instance.deliveries[id_pack].point.lat
        )
        delivery = Delivery(
          id_pack,
          point,
          instance.deliveries[id_pack].size,
          instance.deliveries[id_pack].idu
        )
        vehicle.append(delivery)
    vehicleConstruct = CVRPSolutionVehicle(origin=instance.origin, deliveries=vehicle)
    vehicles.append(vehicleConstruct)
  solution = CVRPSolution(name=name, vehicles=vehicles)
  return solution
  
def solutionJson(
  instance: CVRPInstance, 
  vehiclesPossibles
  )-> CVRPSolutionKpprrf:
  name = instance.name
  vehicles = []
  for k, v in vehiclesPossibles.items():
    vehicle = []
    dep = 0
    for id_pack in v:
      if dep == 0:
        dep += 1
        continue
      else:
        point = Point(
          lng=instance.deliveries[id_pack].point.lng, 
          lat=instance.deliveries[id_pack].point.lat
        )
        delivery = Delivery(
          id_pack,
          point,
          instance.deliveries[id_pack].size,
          instance.deliveries[id_pack].idu
        )
        vehicle.append(delivery)
    vehicleConstruct = CVRPSolutionVehicle(origin=instance.origin, deliveries=vehicle)
    vehicles.append(vehicleConstruct)
  solution = CVRPSolution(name=name, vehicles=vehicles)
  return solution

def solutionJsonWithTime(
  time_exec: float,
  instance: CVRPInstance, 
  vehiclesPossibles,
  namePathSolution
  )-> CVRPSolutionOpt:
  name = instance.name
  vehicles = []
  for k, v in vehiclesPossibles.items():
    vehicle = []
    dep = 0
    for id_pack in v:
      if dep == 0:
        dep += 1
        continue
      else:
        point = Point(
          lng=instance.deliveries[id_pack].point.lng, 
          lat=instance.deliveries[id_pack].point.lat
        )
        delivery = Delivery(
          id_pack,
          point,
          instance.deliveries[id_pack].size,
          instance.deliveries[id_pack].idu
        )
        vehicle.append(delivery)
    vehicleConstruct = CVRPSolutionVehicle(origin=instance.origin, deliveries=vehicle)
    vehicles.append(vehicleConstruct)
  solution = CVRPSolutionOpt(name=name, vehicles=vehicles, time_exec = time_exec)
  solution.to_file(namePathSolution)
  return solution

def selectVehicleWeakness(instance, vehicles, rule, matrix_distance):
  vehicleSelect = {}
  if rule == 'capacity':
    capacity_min = 380
    min_c = 0
    for vehicle, id_packets in vehicles:
      capacity = sum([instance[d].size for d in id_packets])
      if capacity < capacity_min:
        capacity_min = capacity
        min_c = vehicle
    vehicleSelect[min_c] = vehicles[min_c] 
    return vehicleSelect   

  elif rule == 'distance':
    distance_per_packet_min = 9999999999
    idx_v = 0
    for vehicle, deliveries in vehicles:
      distance = calculate_distance(vehicles[vehicle], matrix_distance)/len(deliveries)
      if distance < distance_per_packet_min:
        distance_per_packet_min = distance
        idx_v = vehicle
    vehicleSelect[idx_v] = vehicles[idx_v] 
    return vehicleSelect

  else:
    print("Não implementado!")
    return vehicleSelect

def calculate_distance(indexes_points, matrix_distance):
  distance = 0
  for i in range(1,len(indexes_points)):
    distance += matrix_distance[indexes_points[i-1]][indexes_points[i]]
  return round(distance/1_000, 4)

def reduceVehicles(instance, solution, vehiclesPossibles, matrix_distance):
  # reduzir o numero de veiculos
  vehicles_occupation = {}
  for v in range(0,len(vehiclesPossibles)):
    # acabar com os veiculos vazios
    if len(vehiclesPossibles[v]) != 0:
      vehicles_occupation[v] = vehiclesPossibles[v] #indices
  # selecionar um veiculo fraco (por capacidade ou por distancia/packet)
  vehicle, id_vehicle = selectVehicleWeak(instance, solution)
  if vehicle != None:
    # feito assim para saber a distancia do dep -> cliente
    route_weak = [d.idu+1 for d in vehicle]
    route_weak.insert(0,0)
    # selecionar o pior pacote do veiculo
    #   sera o pacote que mais compensa retirar do veiculo fraco
    # colocar o pacote em uma rota proxima que nao seja a anterior
  # destruir a rota existente
  # criar lista de pacotes não vizitados (pacotes do veiculo fraco)
  # percorrer os pacotes não vizitados
  # selecionar rotas vizinhas do pacote (atraves dos T pacotes existentes)
  # caso uma rota vizinha esteja lotada
  #   - Pesquisar 
  #       - 'pacotes ruins' dentro da rota vizinha: 
  #         - 1. avaliar a retirada de 1 pacote da rota 
  #         - 2. se for possivel inserir 'o pacote nao visitado' após a retirada do 'pacote ruim'
  #           - 2.1. Avaliar o ganho da retirada do 'pacote ruim' montar dicio : 
  # {
  #       packet_id: ganho da retirada dele com a inserção do pacote nao vizitado,
  #       
  # } 
  #           - 2.2. Tentar retirar outro pacote juntamente com o pacote anterior
  #   - Tentar inserir o pacote selecionado retirando 'pacotes ruins'  
  #   - Selecionar n 'pacotes ruins' até ser possível inserir o pacote selecionado
  #   - Inserir o pacote selecionado da melhor maneira