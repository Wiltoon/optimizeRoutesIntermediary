lenght = int(input())                  # Reading input from STDIN
inp = input()
arr = []
for i in range(lenght):
    arr.append(int(inp.split(" ")[i]))
sumarr = sum(arr)
minValue = 100000
for el in arr:
    value = el*lenght
    if value > sumarr:
        if el < minValue:
            minValue = el
print('%d' %minValue)         # Writing output to STDOUT