import copy

from .twoopt import *
from .computeDistances import * 
from .conditions import *
from .operations import *
from .classes.types import *
from .classes.task1 import *

## Essa função deve colocar os packets nos melhores vizinhos
def reallocatePacksVehicle(
    instance: CVRPInstance, 
    vehicle: list, 
    vehiclesPossibles, 
    route_weak,
    id_vehicle: int,
    matrix_distance,
    T: int) -> CVRPSolution:
  index = 0
  # print("v =" + str(id_vehicle))
  for pack_free in vehicle:
    neighs = {}
    packs_neigs = []
    # print(route_weak[index])
    id_pack = route_weak[index]
    index += 1 # cada vez pega outro pacote da rota fraca
    # Dicionario com chave: id delivery, valor: distancia do pacote atual ate outro pacote
    # Construir matrix distance
    for i in range(len(instance.deliveries)):
      neighs[i] = matrix_distance[pack_free.idu][i]
    # Aqui temos um vetor ordenado de todos os pacotes proximos
    for id in sorted(neighs, key = neighs.get):
      packs_neigs.append(id)
    # print(packs_neigs)
    # Preciso de uma relação de quais pacotes estão em quais veículos 
    # (vehiclesPossibles (dicionario [chave: id_vehicle, valor: list(id_deliveries)]))
    routes_neighs = []
    auxT = 0
    for d in packs_neigs:
      if auxT < T:
        for k, v in vehiclesPossibles.items():
          if k == id_vehicle:
            continue
          if canAddPacket(id_pack, v, instance):
            routes_neighs.append(k)
            auxT += 1
      else:
        break
    # solução parcial em dict
    insertionPackInNeighborhood(
      vehiclesPossibles, #id vehicle: [ids_packs]
      routes_neighs, #ids das rotas vizinhas
      id_pack,
      id_vehicle,
      matrix_distance
    )
  # print(vehiclesPossibles)
  solution_partial = solutionJson(instance, vehiclesPossibles)
  return solution_partial
    

# Deve retornar um new_solution: CVRPSolution
def rotineIntermediary(
    instance: CVRPInstance,
    solution: CVRPSolution,
    osrm_config: OSRMConfig,
    T: int # numero de pacotes próximos
  ) -> CVRPSolution:
  MAX_ = instance.vehicle_capacity
  new_solution = copy.copy(solution)
  points = [d.point for d in instance.deliveries]
  matrix_distance = calculate_distance_matrix_m(
    points, osrm_config
  )
  while limitVehicleTotal(instance, new_solution):
    s = copy.copy(new_solution)
    vehicle, id_vehicle = selectVehicleWeak(instance, new_solution)
    vehiclesPossibles = createVehiclesPossibles(new_solution)
    route_weak = [d.idu for d in vehicle]
    new_solution = reallocatePacksVehicle( # aqui deve ser feito a realocação dos pacotes da rota fraca
        instance, vehicle, vehiclesPossibles, 
        route_weak, id_vehicle, matrix_distance, T
    )
    if isBetterThan(instance, s, new_solution, osrm_config):
      break
  for k, v in vehiclesPossibles:
    vehiclesPossibles[k] = twoOpt(
      current_tour=v,
      matrix_distance=matrix_distance
    )
  new_solution = solutionJson(instance, vehiclesPossibles)
  return new_solution
  
def isBetterThan(
  instance: CVRPInstance,
  solution: CVRPSolution, 
  new_solution: CVRPSolution, 
  osrm_config: OSRMConfig):
  sol = evaluate_solution(instance, solution, osrm_config)
  print(sol)
  # sol = len(solution.deliveries)
  n_sol = evaluate_solution(instance, new_solution, osrm_config)
  print(n_sol)
  # n_sol = len(new_solution.deliveries)
  return sol >= n_sol

