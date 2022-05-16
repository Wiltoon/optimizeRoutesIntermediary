from src.classes.types import *
from src.classes.distances import *
from src.classes.task1 import *
from matplotlib import pyplot as plt

def plot_bar_horizontais(solutions, methods, colors, osrm_config: OSRMConfig):
  axis_met_x = []
  axis_met_c = []
  axis_met_p = []
  axis_met_d = [] 
  dif = 0.4
  for s in range(len(solutions)):
    axis_x = []
    axis_c = []
    axis_p = []
    solution = solutions[s]
    clr = colors[s]
    sol = CVRPSolution.from_file(solution)
    axis_d = [
        round(calculate_route_distance_m(v.no_return, config=osrm_config)/1_000, 4)
        for v in sol.vehicles
    ]
    for i in range(len(sol.vehicles)):
      axis_x.append(i+dif*s)
      carga_used = 0
      n_deliveries = 0
      for d in sol.vehicles[i].deliveries:
        carga_used += d.size
        n_deliveries += 1
      axis_c.append(carga_used)
      axis_p.append(n_deliveries)
    axis_met_x.append(axis_x)
    axis_met_c.append(axis_c)
    axis_met_p.append(axis_p)
    axis_met_d.append(axis_d)
  fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20,5))
  for s in range(len(axis_met_x)):
    solution = solutions[s]
    method = methods[s]
    clr = colors[s]
    ax1.barh(axis_met_x[s], axis_met_c[s], height=dif, color=clr, label=method)
    ax2.barh(axis_met_x[s], axis_met_p[s], height=dif, color=clr, label=method)
    ax3.barh(axis_met_x[s], axis_met_d[s], height=dif, color=clr, label=method)
  ax1.set(
      title="Capacidade utilizada por veículo/rota",
      ylabel="veículo",
      xlabel="Capacidade utilizada"
      )
  ax2.set(
      title="Número de pacotes atendidos/veículo",
      ylabel="veículo",
      xlabel="Pacotes atendidos"
      )
  ax3.set(
      title="Distância percorrida pelo veículo",
      ylabel="veículo",
      xlabel="Distância percorrida"
      )
  plt.show()

def compare_solutions(solutions_paths, instance, osrm_config:OSRMConfig):
    # Existem n solutions
    n_solutions = len(solutions_paths)
    methods = [meth.split('/')[1] for meth in solutions_paths]
    colors = ['red','blue']
    print(methods)
    print(colors)
    # Nome da Instancia 
    for ps in solutions_paths:
        print(ps)
        inst = CVRPInstance.from_file(instance)
        solution = CVRPSolution.from_file(ps)
        print("Total distance = " + str(evaluate_solution(inst, solution, osrm_config)))
    plot_bar_horizontais(solutions_paths, methods, colors, osrm_config)

if __name__ == '__main__':
    osrm_config = OSRMConfig(host="http://ec2-34-222-175-250.us-west-2.compute.amazonaws.com")
    city = "pa"
    paths = ["resources/kpprrf/pa-0/", "out/kpprrf/pa-0/"]
    input = "./inputs/"+city+"-0/"
    n = 3
    extJson = ".json"
    for i in range(n):
        instance = "cvrp-0-"+city+"-"+str(i)+extJson
        solution_paths = [meth+instance for meth in paths]
        input_instance = input+instance
        compare_solutions(solution_paths, input_instance, osrm_config)
        