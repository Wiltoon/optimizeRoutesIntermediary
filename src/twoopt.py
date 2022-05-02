def betterTour(new_tour, best_tour, matrix_distance):
    new_distance = 0
    best_distance = 0
    for i in range(len(best_tour)-1):
        best_distance += matrix_distance[best_tour[i]][best_tour[i+1]]
        new_distance += matrix_distance[new_tour[i]][new_tour[i+1]]
    return new_distance < best_distance

def twoOpt(current_tour, matrix_distance):
    n = len(current_tour)
    best_tour = current_tour.copy()
    for i in range(1,n-2):
        for j in range(i+1, n):
            if (j-i) == 1:
                continue
            else:
                c_vet = slice(0,i)
                f_part = current_tour[c_vet]
                s_vet = slice(i,j)
                s_part = current_tour[s_vet].reverse()
                t_vet = slice(j,n)
                t_part = current_tour[t_vet]
                new_tour = [*f_part, *s_part, *t_part]
                if betterTour(new_tour, best_tour, matrix_distance):
                    best_tour = new_tour
    return best_tour
