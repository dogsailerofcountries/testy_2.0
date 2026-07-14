total = 0
n = int(input(""))
for i in range(n):
    line = input("")
    lineQ = 0
    if int(line[0]) == 1:
        lineQ += 1
    if int(line[2]) == 1:
        lineQ += 1
    if int(line[4]) == 1:
        lineQ += 1
    if lineQ >= 2:
        total += 1
print(total)
