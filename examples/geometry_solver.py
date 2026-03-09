from sympy import *

def solve():
    # Triangle with AB = AC, angle bisector divides BC = BD + DC = 3 + 5 = 8
    # By angle bisector theorem, BD/DC = AB/AC = 3/5
    # But since AB = AC, ratio should be 1, but 3/5 != 1, contradiction
    # Therefore, no such triangle
    return r"\boxed{\text{No solution}}"

if __name__ == "__main__":
    result = solve()
    print(result)
