from base64 import b64encode

file = open(input(), 'rb')
b64 = b64encode(file.read())
print(b64)
open('out.dat', 'w').write(b64.decode())
