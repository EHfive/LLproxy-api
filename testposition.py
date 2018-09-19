f = lambda x: (x - 1) % 3 * 13 + (x - 1) // 3 + 1
def position(x):
    row = (x - 1) % 3
    col = (x - 1) // 3 + 1
    if 2 >= col >= 1:
        return row * 10 + col
    elif 8 >= col >= 3:
        return row * 10 + col + 2
    elif 10 >= col >= 9:
        return row * 10 + col - 6
    elif 13 >= col >= 11:
        if row == 0:
            return 23 + col
        elif row == 1:
            return 20 + col
        elif row == 2:
            return 26 + col
    return False
for n in range(1, 40):
    print((n - 1) % 3 + 1, '行', (n - 1) // 3 + 1, '列', 'skill_id:', n, position(n))



