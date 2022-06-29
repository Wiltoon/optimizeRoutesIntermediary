import requests
from .classes.types import *
from .classes.distances import *

def calculateDiferenceDistanceRoute(
    matrix_distance, 
    old_possible,
    possible # lista com pacotes de como sera atendido
    ):
  """Calcular a diferença entre uma rota antiga por uma rota nova"""
  distanceOld = 0 
  distanceNew = 0 
  # print("OLDER =>")
  # print(old_possible)
  # print("ACTUAL =>")
  # print(possible)
  for old in range(len(old_possible)-1):
    dest = old + 1
    distanceOld += matrix_distance[old_possible[old]+1][old_possible[dest]+1]
  for o in range(len(possible)-1):
    d = o + 1
    distanceNew += matrix_distance[possible[o]+1][possible[d]+1]
  distance = distanceNew - distanceOld
  # retorna a distancia percorrida pela rota
  return distance

def calculateDistanceRoutes(routes, matrix_distance):
  """Calcular a distancia percorrida por uma lista de rota"""
  distance = []
  # print(possible)´
  for route in routes:
    distance.append(computeDistanceRoute(route, matrix_distance))
  # retorna a distancia percorrida pela rota
  return sum(distance)


def computeDistanceRoute(route, matrix_distance):
  """Retorna a distancia percorrida pela rota"""
  distance = 0
  for o in range(len(route)-1):
    d = o + 1
    distance += matrix_distance[route[o]+1][route[d]+1]
  return distance

def distance_osrm(
    p_origin: Delivery,
    p_destiny: Delivery,
    osrm_config: OSRMConfig
):
  config = osrm_config
  points = []
  points.append(p_origin.point)
  points.append(p_destiny.point)
  coords_uri = ";".join(
        ["{},{}".format(point.lng, point.lat) for point in points]
    )
  response = requests.get(
        f"{config.host}/table/v1/driving/{coords_uri}?annotations=distance",
        timeout=config.timeout_s,
    )

  response.raise_for_status()
  return response.json()["distances"]

def calculateSolutionMatrix(solution: CVRPSolution, matrix_distance):
  newPossible = {}
  for v in range(len(solution.vehicles)):
    newPossible[v] = [0]
    for d in solution.vehicles[v].deliveries:
      newPossible[v].append(d.idu+1)
    # print(newPossible[v])
  route_distances_m = 0
  for k, v in newPossible.items():
    for i in range(len(v)-1):
      route_distances_m += round(matrix_distance[v[i]][v[i+1]], 1)
  return round(route_distances_m / 1_000, 4)