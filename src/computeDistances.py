import requests
from .classes.types import *
from .classes.distances import *

def calculateDistanceRoute(
    matrix_distance, 
    old_possible,
    possible # lista com pacotes de como sera atendido
    ):
  # calcular a distancia percorrida pela rota desta forma
  points = []
  distanceOld = 0 
  distanceNew = 0 
  # print(possible)
  for old in range(len(old_possible)-1):
    dest = old + 1
    distanceOld += matrix_distance[old][dest]
  for o in range(len(possible)-1):
    d = o + 1
    distanceNew += matrix_distance[o][d]
  distance = distanceNew - distanceOld
  # retorna a distancia percorrida pela rota
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
