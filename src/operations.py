from classes.types import *
# Essa função deve decidir em qual rota vizinha o pacote deve ser inserido
# e retornar a solução final de como ficará as rotas
def insertionPackInNeighborhood(
    instance: CVRPInstance,
    vehiclesPossibles,
    routes_neighs, 
    id_pack: int
    ):
  best_values = []
  best_routes = []
  neighbors = list(dict.fromkeys(routes_neighs)) # neighbors retorna uma lista de rotas vizinhas sem repetição de rotas
  for id_route in neighbors:
    route, min_value = insertPacketInRoute(instance, id_pack, vehiclesPossibles[id_route])
    best_values.append(min_value) # calcula a distancia da melhor posição para o pacote ficar na rota
    best_routes.append(route)     # lista das rotas vizinhas construidas com o pacote
  id_b = best_values.index(min(best_values, key = float))
  id_best_route = neighbors[id_b]
  route_incluse = best_routes[id_b]
  solution = create_new_solution(instance, vehiclesPossibles, route_incluse) # teoricamente o vehiclesPossibles precisa estar com a resposta final
  return solution


def createVehiclesPossibles(solution: CVRPSolution):
  #enumere as rotas da solution
  #enumere os pacotes 
  #chave id_route 
  #valor [id_packs]
  vehiclesPossible = {}
  for v in range(len(solution.vehicles)):
    vehiclesPossible[v] = []
    for d in v.deliveries:
      vehiclesPossible[v].append(d.idu)
  return vehiclesPossible

# dado o dicionario transformar ele em resposta cvrp solution
def create_new_solution(instance, vehiclesPossibles, route_incluse):
  print(vehiclesPossibles)
  return solution


# Essa função deve avaliar determinado pacote em uma rota e qual o melhor resultado
def insertPacketInRoute(
    instance: CVRPInstance,
    id_pack, 
    route_select):
  p_insertion = []
  for i in range(len(route_select)+1):
    route_aux = [el for el in route_select]
    p_insertion.append(route_aux.insert(i, id_pack))
  scores = []
  for possible in p_insertion:
    score = calculateDistanceRoute(instance, possible)
    scores.append(score)
  route = p_insertion[scores.index(min(scores, key = float))] # lista de pacotes arranjado da melhor forma
  return route, min(scores, key = float)

def selectVehicleWeak(dictVehicles, vehicles_ordened, MAX_: int):
  minVehicles = sum([d.size for k, v in dictVehicles.items() for d in v.deliveries])/MAX_
  sumVehicles = len(dictVehicles)
  if sumVehicles <= minVehicles:
    return None, -1
  weak = vehicles_ordened[0]
  vehicleWeak = dictVehicles[weak]
  sizeUsed = sum([d.size for d in vehicleWeak.deliveries])
  if sizeUsed > 0.9*MAX_:
    return None, -1
  else:
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