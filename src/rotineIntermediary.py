import copy
from itertools import combinations
import time

from .twoopt import *
from .interRoute import *
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

  index = 1
  # print(len(instance.deliveries))
  # print(route_weak)
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
            # print(k, v)
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
    T: int, # numero de pacotes próximos
    city: str
  ) -> CVRPSolution:
  origin = [instance.origin]
  deliveries = [d.point for d in instance.deliveries]
  points = [*origin, *deliveries]
  # print(len(points))
  matrix_distance = calculate_distance_matrix_m(
    points, osrm_config
  )
  vehP = createVehiclesPossibles(solution)
  psolution = solutionJson(instance, vehP)
  sol = calculateSolutionMatrix(psolution, matrix_distance)
  new_solution = copy.copy(solution)
  start_t = time.time()
  while limitVehicleTotal(instance, new_solution):
    s = copy.copy(new_solution)
    vehicle, id_vehicle = selectVehicleWeak(instance, new_solution)
    vehiclesPossibles = createVehiclesPossibles(new_solution)
    if vehicle != None:
      # print("Numero de veículos utilizados = "+ str(len(vehiclesPossibles)))
      route_weak = [d.idu+1 for d in vehicle]
      route_weak.insert(0,0)
      new_solution = reallocatePacksVehicle( # aqui deve ser feito a realocação dos pacotes da rota fraca
          instance, vehicle, vehiclesPossibles, 
          route_weak, id_vehicle, matrix_distance, T
      )
      if isBetterThan(s, new_solution):
        break
    else:
      break
  finish_t = time.time()
  time_t = finish_t - start_t
  fileNamePath = "out/krs/"+city+"/"+instance.name+".json"
  new_solution_t = solutionJsonWithTime(
    time_t, 
    instance, 
    vehiclesPossibles, 
    fileNamePath
  )
  allin = [f for f in range(len(vehiclesPossibles))]
  combs = [p for p in list(combinations(allin,2))]
  # sol2 = calculateSolutionMatrix(new_solution, matrix_distance)
  # print(sol2)
  start_time_opts = time.time()
  for i in range(10):
    for comb in combs:
      vehiclesPossibles[comb[0]], vehiclesPossibles[comb[1]] = twoOptStar(
        vehiclesPossibles[comb[0]],
        vehiclesPossibles[comb[1]],
        matrix_distance,
        instance
      )
    new_solution = solutionJson(instance, vehiclesPossibles)
    # sol2 = calculateSolutionMatrix(new_solution, matrix_distance)
    # print(sol2)
    for comb in combs:
      vehiclesPossibles[comb[0]], vehiclesPossibles[comb[1]] = twoOptStarModificated(
        vehiclesPossibles[comb[0]],
        vehiclesPossibles[comb[1]],
        matrix_distance,
        instance
      )
    new_solution = solutionJson(instance, vehiclesPossibles)
    # sol2 = calculateSolutionMatrix(new_solution, matrix_distance)
    # print("star mod "+str(i)+" = "+str(sol2))
  finish_time_opts = time.time()
  time_exec = finish_time_opts - start_time_opts
  fileNamePath = "out/krso/"+city+"/"+instance.name+".json"
  new_solution_t = solutionJsonWithTime(
    time_exec, 
    instance, 
    vehiclesPossibles, 
    fileNamePath
  )
  # for k, v in vehiclesPossibles.items():
  #   vehiclesPossibles[k] = twoOpt(current_tour=v,matrix_distance=matrix_distance)
  # sol2 = calculateSolutionMatrix(new_solution, matrix_distance)
  # print(sol2)
  return new_solution
  
def isBetterThan(
  solution: CVRPSolution, 
  new_solution: CVRPSolution):
  sol = len(solution.vehicles)
  # print(sol)
  n_sol = len(new_solution.vehicles)
  # print(n_sol)
  return sol <= n_sol

