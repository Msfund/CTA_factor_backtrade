# encoding: utf-8

# 本文件用于定义自己所需要的错误类型

class NameError(Exception):
    def __init__(self, name):
        print("the name: '%s'  is unvalid"%name)



def mytry(data):
    try:
        print(data1)
    except :
        raise NameError(data)