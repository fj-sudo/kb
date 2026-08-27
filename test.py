def outer():
    a=10
    def inter():
        nonlocal a
        a+=10
        print("inter:", a)
        return 1
    print("outer:",a)
    return inter
f=outer()
f()



