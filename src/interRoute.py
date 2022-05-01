# Here we have 2opt* with aim of swap 1 route's pack for another route's pack 
def compensation(md, r1, r2, i, j):
    if i != (len(r1)-1):
        if i-1 == 0:
            gain = md[r1[i-1]][r2[j]+1] + md[r2[j]+1][r1[i+1]+1]
            lose = md[r1[i-1]][r1[i]+1] + md[r1[i]+1][r1[i+1]+1]
        else:
            gain = md[r1[i-1]+1][r2[j]+1] + md[r2[j]+1][r1[i+1]+1]
            lose = md[r1[i-1]+1][r1[i]+1] + md[r1[i]+1][r1[i+1]+1]
    else:
        if i-1 == 0:
            gain = md[r1[i-1]][r2[j]+1]
            lose = md[r1[i-1]][r1[i]+1]
        else:
            gain = md[r1[i-1]+1][r2[j]+1]
            lose = md[r1[i-1]+1][r1[i]+1]
    return gain, lose

def twoOptStar(route1, route2, md):
    # print(route1)
    # print(route2)
    for p1 in range(1,len(route1)):
        for p2 in range(1,len(route2)):
            gain1, lose1 = compensation(md, route1, route2, p1, p2)
            gain2, lose2 = compensation(md, route2, route1, p2, p1)
            lose = lose1 + lose2
            gain = gain1 + gain2
            if lose > gain:
                new_route1 = [route1[i] for i in range(len(route1)) if i != p1]
                new_route1.insert(p1, route2[p2])
                new_route2 = [route2[j] for j in range(len(route2)) if j != p2]
                new_route2.insert(p2, route1[p1])
                route1 = new_route1.copy()
                route2 = new_route2.copy()
                
    return route1, route2
