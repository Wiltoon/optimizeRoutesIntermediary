from computeDistances import *
from conditions import *
from operations import *
from classes.types import *

## Essa função deve colocar o packet no melhor vizinho
def reallocatePacksVehicle(
    instance: CVRPInstance, 
    vehicle: CVRPSolutionVehicle, 
    vehiclesPossibles, 
    route_weak,
    id_vehicle: int,
    T: int):
  index = 0
  MAX_ = instance.capacity
  for pack_free in vehicle.deliveries:
    neighs = {}
    packs_neigs = []
    id_pack = route_weak[index]
    index += 1
    # Dicionario com chave: id delivery, valor: distancia do pacote atual ate outro pacote
    for i in range(len(instance.deliveries)):
      neighs[i] = distance_osrm(pack_free, instance.deliveries[i])
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
    new_solution = insertionPackInNeighborhood(
        instance,
        vehiclesPossibles, 
        routes_neighs, 
        id_pack
    )

def rotineIntermediary(
    instance: CVRPInstance,
    solution: CVRPSolution,
    T: int # numero de pacotes próximos
  ):
  new_solution = solution
  while limitVehicleTotal(instance, new_solution):
    vehicle, id_vehicle = selectVehicleWeak(instance, new_solution)
    vehiclesPossibles = createVehiclesPossibles(new_solution)
    route_weak = [d.idu for d in vehicle]
    new_solution = reallocatePacksVehicle( # aqui deve ser feito a realocação dos pacotes da rota fraca
        instance, vehicle, vehiclesPossibles, 
        route_weak, id_vehicle, T
    )
  return new_solution
  