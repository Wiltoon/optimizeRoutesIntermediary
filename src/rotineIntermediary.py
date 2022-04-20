from .computeDistances import * 
from .conditions import *
from .operations import *
from .classes.types import *

## Essa função deve colocar os packets nos melhores vizinhos
def reallocatePacksVehicle(
    instance: CVRPInstance, 
    vehicle: CVRPSolutionVehicle, 
    vehiclesPossibles, 
    route_weak,
    id_vehicle: int,
    osrm_config: OSRMConfig,
    T: int) -> CVRPSolution:
  index = 0
  MAX_ = instance.vehicle_capacity
  print("v =" + str(id_vehicle))
  for pack_free in vehicle.deliveries:
    neighs = {}
    packs_neigs = []
    id_pack = route_weak[index]
    index += 1 # cada vez pega outro pacote da rota fraca
    # Dicionario com chave: id delivery, valor: distancia do pacote atual ate outro pacote
    for i in range(len(instance.deliveries)):
      neighs[i] = distance_osrm(pack_free, instance.deliveries[i], osrm_config)
    # Aqui temos um vetor ordenado de todos os pacotes proximos
    for id in sorted(neighs, key = neighs.get):
      packs_neigs.append(id)
    # Preciso de uma relação de quais pacotes estão em quais veículos 
    # (vehiclesPossibles (dicionario [chave: id_vehicle, valor: list(id_deliveries)]))
    routes_neighs = []
    auxT = 0
    for d in packs_neigs:
      if auxT < T:
        for k, v in vehiclesPossibles.values():
          if k == id_vehicle:
            continue
          if canAddPacket(id_pack, v, instance):
            routes_neighs.append(k)
            auxT += 1
      else:
        break
    # solução parcial em dict
    insertionPackInNeighborhood(
        instance,
        vehiclesPossibles, #id vehicle: [ids_packs]
        routes_neighs, #ids das rotas vizinhas
        id_pack,
        id_vehicle
    )
    

# Deve retornar um new_solution: CVRPSolution
def rotineIntermediary(
    instance: CVRPInstance,
    solution: CVRPSolution,
    osrm_config: OSRMConfig,
    T: int # numero de pacotes próximos
  ) -> CVRPSolution:
  MAX_ = instance.vehicle_capacity
  new_solution = solution
  while limitVehicleTotal(instance, new_solution):
    vehicle, id_vehicle = selectVehicleWeak(instance, new_solution)
    vehiclesPossibles = createVehiclesPossibles(new_solution)
    route_weak = [d.idu for d in vehicle]
    new_solution = reallocatePacksVehicle( # aqui deve ser feito a realocação dos pacotes da rota fraca
        instance, vehicle, vehiclesPossibles, 
        route_weak, id_vehicle, osrm_config, T
    )
  return new_solution
  