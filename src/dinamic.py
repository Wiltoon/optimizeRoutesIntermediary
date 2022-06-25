def collectBatchs(batch):
    # percorrer a fila dos pacotes dinamicos
    # tira o primeiro pacote dinamico do batch
    # roteiriza o pacote dinamico

def routingPack(solution_initial, packet, matrix_d, instance, batch):
    #devolve lista das rotas vizinhas do pack dinamico
    trying = 0
    routes_neig = lookForNeighboringRoutes(packet, solution_initial) 
    for rSelect in routes_neig:
        try:
            insertionPackInRoute(packet, rSelect, batch)
            break
        except NoRouterFound:
            trying += 1
    if trying == len(routes_neig): # sem rotas vizinhas do pack dinamico
        newRoute = createNewRoute(packet, solution_initial)
        r1, r2 = twoOptStarModificated(newRoute, routes_neig[0], matrix_d, instance)
        newRoute = r1.copy() # modificar a nova rota
        routes_neig[0] = r2.copy() # modificar a rota vizinha
        createNewSolution(newRoute, solution_initial)
    
    

            
            