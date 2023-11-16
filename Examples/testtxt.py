
text = open("macgw.txt", "r")
macy = text.read()
print(str(macy))
print(type(macy))


with open("macgw.txt", "r") as f:
   contenido = f.read()
macy = eval(contenido)
print(macy)
print(type(macy))
