from audioop import reverse

def twoOpt(current_tour){
    n = len(current_tour)
    best_tour = current_tour.copy()
    for(int i=1; i<n-2; i = i+1){
        for(int j = i+1; j < n+1; j = j+1){
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
                if(betterTour(new_tour, best_tour):
                    best_tour = new_tour
        }
    }
}