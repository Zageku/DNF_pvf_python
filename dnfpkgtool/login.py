
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
import base64
import struct
public_key_str = '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsz6g1F4gCkpSuwUSk4Di
y1SxXVHEHKen2A2e+JCRxYuPGvJEYlaJpmaGABEeydzStronNX7O5Fdo1rQ2RHwu
OFPNnugAUk138HlsK+v2MHpur9mzRK2L6C7amgxtBu+mFXV8wcwvuuDp1a+LFzCo
Roms+KwxnYbC9SM/VUB1pQEZOrYF6kN1DxRtnkIzJ/4kdVkymNKz3rEDLtwXMnlx
bQn7jivGoUNbXeTqdEDKXDFRbXWpxtUxiklC949h0dtoYLmALmt/bWKbK+DpwwJL
c0BD/nEJKhP/x4YubwBaHdcagZlIX+rQQnABt+yaNYbYWKoV8eHGifAH9OEYnL/T
UwIDAQAB
-----END PUBLIC KEY-----
'''

private_key_str = '''-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA4WPn+6Fmt8bpHwDV4QqVFzno+z2xzDhzc680ZkNhzVUEX95m
uDfVntqZlYRWtfcjklo6m1/sp3DNosq4ASQgFgf+gKDZDWqekprQcZuHaBfGgw5r
1OUnAkJFYbgLKVem/2B8mKyZivDkKdrcPmYih77zt0kWRBroxDwv7k4Ia0vhEdaK
tvEMGxoVoRZcmZVJA/pslFnICFSzJoQK+WWMfN2ONEucSe5NdnbRjbkT0QFG9+/m
UXFk9O6F3vTvnUekNlNFVAGq6dygLzmAoYL/wME/CcaxG0rlv4PzrZwHRkaK36ZH
sLtu5ASj2IZlsUjXVWzs64JsZ3XTHUEqkIkWTQIDAQABAoIBAQDe6SAWDZq5R1Bo
CTt+RikNv4hccrfVcj88uproSNwBZ4PcDOkqaI4tfaVH6oqXjMTxiatM36H+N+Io
jrVM652QLHfYXzxLuJb8B4D/2wIgQONj2m9rLvdVlJVp/8uKJ9ZR2+teU9XHRFdj
zcDlNb4Q4xnGu9H5qWNsMNp2pVZORfICXAvWc53VxP07s5XrSy/fXEPv47iGWeXV
x+HIPxYHTqfiTVEWQEuRPxvV0wxb412EpqOtGkIaTkdlQ+m5TpEo5GE+4IgHRr3U
RmItQWQkoUj27QugkKdUyJ9nM4KRob+cGM5pmVFOKAMG4o1Y1DSsHI3/r1bccteb
IOnLHKwBAoGBAPfyt3H7TP6we2SxYmaofOu2SHYll7XTPfYnk2UXCSZVxHCPMBNu
T7NqezSa1/2BIFZEmdwPeFfWMbP8OTbOaDIz2tIp8gLletcmGJwdiIvcQgqS8mH1
+52m0+HAXuGibwa06gX/CT2lUlugTeHvRS9/umMCEFDUvJiSJjJFmnEdAoGBAOi1
qGzFgFSpnQlHegFSOGxNVM0eaG2sQ36wBPd3r4Gd8rJmhlHNNK5TegNd/3mYLIvv
7Eh9QdqsSo7SkvcxG3BGITOkJT3R5QUG1jwWo12PqzKZX3PvKrlh3e66a02vU3+g
HfoFtsMxtG0Q9IA8uz6toJ1j/WzbjFhAsSnKHeLxAoGBAJUhnYim98Zwa6dCscbB
LHGxr5+wOLGaHriBUTwKQOyXxZFV7jqhrLpjHzuirqrBEawRkuEzRNS/9iElYVw/
hZg8bC7gH7nyQJJLTZ4IfWpxzh8CB1s4UmCeSO6NgAQCaPkFs4Rrwyka2JBXuMBd
46UQFBEc2qdjbRPvQ54VEzFZAoGAeILSpPmmmrF3rH2CdjqxE4z8lHjh1aH3Fh1r
hQhLMFGuhKrJdoVRedGrByFfkwW2VAW8lFGhj+/XcJ0mFLMupXb77LVdv+T5uB+x
RE7o7SPgoYSBxRUfR/+hoeaSeRmJoTc3LupUmkMcT7sPE3Xf9faOjdNhQ0VzKaTe
2mhcD9ECgYBdUbpCjK/D0+Gw9Xb3ZmzA+8q83PftlWtMx+3RfXfC8gssUA6hFFro
zmN3e4dRlCUEd3y5G9TMWF9F3odNY542gGO8JziwXX/BGzB8JuS8uxwkofqqd4Vm
Zvvd6g34siiE6Nj94kfz1BUF6c0grb8hDDUpASHGzktC5fRzUOZRMg==
-----END RSA PRIVATE KEY-----'''

def login(uid):
    public_key = RSA.importKey(public_key_str)
    cipher = PKCS1_cipher.new(public_key)
    data = '%08x010101010101010101010101010101010101010101010101010101010101010155914510010403030101' % uid
    dataInBytes = b''
    for i in range(0,len(data),2):
        dataInBytes += struct.pack('H',int(data[i:i+2],16))


        
    '''dataInBytes = bytes.fromhex(data)
    print(dataInBytes)
    data2 = b'\x00'.join(dataInBytes)
    print(data2)'''
    encryptedStr = cipher.encrypt(dataInBytes)
    return base64.b64encode(encryptedStr).decode()

if __name__=='__main__':
    uid = 8
    print(login(uid))