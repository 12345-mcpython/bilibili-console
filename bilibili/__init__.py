import os


def init():
    if os.path.exists("init"):
        return False
    print("正在初始化LBCC.")
    if not os.path.exists("cached"):
        os.mkdir("cached")
    if not os.path.exists("users"):
        os.mkdir("users")
    with open("init", "w"):
        pass
    print("初始化完成.")
    return True
