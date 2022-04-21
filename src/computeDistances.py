import requests
from .classes.types import *
from .classes.distances import *

def calculateDistanceRoute(
    instance: CVRPInstance, 
    possible, # lista com pacotes de como sera atendido
    osrm_config: OSRMConfig
    ):
  # calcular a distancia percorrida pela rota desta forma
  points = []
  for d in possible:
    points.append(instance.deliveries[d].point)
  # retorna a distancia percorrida pela rota
  return calculate_route_distance_m(points, osrm_config)

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
