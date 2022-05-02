import copy
from itertools import combinations

<<<<<<< HEAD
from .twoopt import *
=======
from .interRoute import twoOptStar

from .twoOpt import *
>>>>>>> dc7184286f98a6db5932631765060aa08c94829f
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
<<<<<<< HEAD
  index = 0
  # print("v =" + str(id_vehicle))
=======
  index = 1
  # print(route_weak)
  # print(route_weak)
>>>>>>> dc7184286f98a6db5932631765060aa08c94829f
  for pack_free in vehicle:
    # print(pack_free)
    neighs = {}
    packs_neigs = []
    id_pack = route_weak[index]
    index += 1 # cada vez pega outro pacote da rota fraca
    # Dicionario com chave: id delivery, valor: distancia do pacote atual ate outro pacote
    for i in range(1,len(instance.deliveries)+1):
      neighs[i] = matrix_distance[pack_free.idu+1][i]
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
  origin = [instance.origin]
  deliveries = [d.point for d in instance.deliveries]
  points = [*origin, *deliveries]
  matrix_distance = calculate_distance_matrix_m(
    points, osrm_config
  )
  vehP = createVehiclesPossibles(solution)
  psolution = solutionJson(instance, vehP)
  sol = calculateSolutionMatrix(psolution, matrix_distance)
  new_solution = copy.copy(solution)
  points = [d.point for d in instance.deliveries]
  matrix_distance = calculate_distance_matrix_m(
    points, osrm_config
  )
  while limitVehicleTotal(instance, new_solution):
    s = copy.copy(new_solution)
    vehicle, id_vehicle = selectVehicleWeak(instance, new_solution)
    vehiclesPossibles = createVehiclesPossibles(new_solution)
    route_weak = [d.idu+1 for d in vehicle]
    route_weak.insert(0,0)
    new_solution = reallocatePacksVehicle( # aqui deve ser feito a realocação dos pacotes da rota fraca
        instance, vehicle, vehiclesPossibles, 
        route_weak, id_vehicle, matrix_distance, T
    )
    if isBetterThan(instance, s, new_solution, osrm_config, matrix_distance):
      break
<<<<<<< HEAD
  for k, v in vehiclesPossibles:
    vehiclesPossibles[k] = twoOpt(
      current_tour=v,
      matrix_distance=matrix_distance
    )
  new_solution = solutionJson(instance, vehiclesPossibles)
=======
    print("Numero de veículos utilizados = "+ str(len(vehiclesPossibles)))
  allin = [f for f in range(len(vehiclesPossibles))]
  combs = [p for p in list(combinations(allin,2))]
  sol2 = calculateSolutionMatrix(new_solution, matrix_distance)
  print(sol2)
  for comb in combs:
    vehiclesPossibles[comb[0]], vehiclesPossibles[comb[1]] = twoOptStar(
      vehiclesPossibles[comb[0]],
      vehiclesPossibles[comb[1]],
      matrix_distance
    )
  new_solution = solutionJson(instance, vehiclesPossibles)
  sol2 = calculateSolutionMatrix(new_solution, matrix_distance)
  print(sol2)
  for k, v in vehiclesPossibles.items():
    vehiclesPossibles[k] = twoOpt(current_tour=v,matrix_distance=matrix_distance)
  sol2 = calculateSolutionMatrix(new_solution, matrix_distance)
  print(sol2)
  print("Solução inicial = "+ str(sol))
>>>>>>> dc7184286f98a6db5932631765060aa08c94829f
  return new_solution
  
def isBetterThan(
  instance: CVRPInstance,
  solution: CVRPSolution, 
  new_solution: CVRPSolution, 
  osrm_config: OSRMConfig,
  matrix_distance):
  # sol = evaluate_solution(instance, solution, osrm_config)
  # print(sol)
  # sol2 = calculateSolutionMatrix(solution, matrix_distance)
  # print("Pela Matrix = " + str(sol2))
  # print("DIFF OSRM = " + str(sol2-sol))
  # route_distances_m = calculateSolutionMatrix(new_solution, matrix_distance)
  # print("Pela Nova Matrix = " + str(route_distances_m))
  sol = len(solution.vehicles)
  print(sol)
  # n_sol = evaluate_solution(instance, new_solution, osrm_config)
  n_sol = len(new_solution.vehicles)
  print(n_sol)
  return sol <= n_sol

