from .classes.types import *

def limitVehicleTotal(instance, solution):
  MAX_ = instance.capacity
  minVehicles = sum([d.size for d in instance.deliveries])/MAX_
  sumVehicles = len(solution.vehicles)
  if sumVehicles <= minVehicles:
    return False
  for v in solution.vehicles:
    sizeUsed = sum([d.size for d in v.deliveries])
    if sizeUsed > 0.9*MAX_:
      return False
  else: 
    return True

def packetNotInRoute(id_pack, route):
  return id_pack not in route

def canAddPacket(
    id_pack: int, 
    route, # lista com id dos pacotes na rota
    instance: CVRPInstance
    ):
  # caso seja possivel inserir o pack_free no v returna True
  pack_free = instance.deliveries[id_pack]
  MAX_ = instance.capacity
  totalSize = 0
  for i in route:
    p_neig = instance.deliveries[i]
    totalSize += p_neig.size
  totalSize += pack_free.size
  return totalSize <= MAX_ and packetNotInRoute(id_pack, route)

