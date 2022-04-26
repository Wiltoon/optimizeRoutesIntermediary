from numpy import matrix
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
    route, min_value = insertPacketInRoute(id_pack, vehiclesPossibles[id_route], matrix_distance)
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
  return vehiclesPossible

# dado o dicionario transformar ele em resposta cvrp solution
def create_new_solution(
  new_route,
  vehiclesPossibles, # modificado
  id_pack_modificated, 
  id_old_route,
  id_new_route
  ):
  # print(vehiclesPossibles)
  vehiclesPossibles[id_old_route].remove(id_pack_modificated)
  if len(vehiclesPossibles[id_old_route]) == 0:
    vehiclesPossibles.pop(id_old_route, 404)
  vehiclesPossibles[id_new_route] = new_route
  # print("============ MODIFICATED ==========")
  # print(vehiclesPossibles)
  # print("-----------------------------------")


# Essa função deve avaliar determinado pacote em uma rota e qual o melhor resultado
def insertPacketInRoute(
    id_pack, 
    route_select,
    matrix_distance):
  p_insertion = []
  for i in range(len(route_select)+1):
    route_aux = [el for el in route_select]
    route_aux.insert(i, id_pack)
    p_insertion.append(route_aux)
  scores = []
  # print(p_insertion)
  for possible in p_insertion:
    score = calculateDistanceRoute(matrix_distance, route_select, possible)
    scores.append(score)
  route = p_insertion[scores.index(min(scores, key = float))] # lista de pacotes arranjado da melhor forma
  return route, min(scores, key = float)

#retornar a rota do veículo de menor uso e seu id
def selectVehicleWeak(instance, solution, matrix_distance):
  MAX_ = instance.vehicle_capacity
  minVehicles = sum([d.size for d in instance.deliveries])/MAX_
  sumVehicles = len(solution.vehicles)
  vehicles_ordened = {}
  if sumVehicles <= minVehicles:
    return None, -1
  for v in range(len(solution.vehicles)):
    vehicles_ordened[v] = densityDelivery(matrix_distance, solution, v)
  sortedDict = sorted(vehicles_ordened.items(), key=lambda x: x[1], reverse=True)
  weak = sortedDict[0][0]
  vehicleWeak = solution.vehicles[weak].deliveries
  return vehicleWeak, weak

def densityDelivery(matrix_distance, solution, v: int):
  distance_total = 0
  total_deliveries = len(solution.vehicles[v].deliveries)
  for o in range(total_deliveries-1):
    d = o + 1
    origin = solution.vehicles[v].deliveries[o].idu
    destiny = solution.vehicles[v].deliveries[d].idu
    distance_total += matrix_distance[origin][destiny]
  return distance_total/total_deliveries

  # for i in sorted(vehicles_ordened, key = vehicles_ordened.get):
  #   sizeUsed = vehicles_ordened[i]
  #   if sizeUsed > 0.5*MAX_:
  #     return None, -1
  #   else:
  #     weak = i
  #     vehicleWeak = solution.vehicles[weak].deliveries
  #     # print("Vehicle Weak:")
      # print(vehicleWeak)
      # print("Index:")
      # print(weak)
      # print("=================")

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
    for id_pack in v:
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