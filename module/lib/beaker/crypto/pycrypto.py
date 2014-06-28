"""Encryption module that uses pycryptopp or pycrypto"""
try:
    # Pycryptopp is preferred over Crypto because Crypto has had
    # various periods of not being maintained, and pycryptopp uses
    # the Crypto++ library which is generally considered the 'gold standard'
    # of crypto implementations
    from pycryptopp.cipher import aes

    def aesEncrypt(data, key):
        cipher = aes.AES(key)
        return cipher.process(data)
    
    # magic.
    aesDecrypt = aesEncrypt
    
except ImportError:
    from Crypto.Cipher import AES

    def aesEncrypt(data, key):
        cipher = AES.new(key)
        
        data = data + (" " * (16 - (len(data) % 16)))
        return cipher.encrypt(data)

    def aesDecrypt(data, key):
        cipher = AES.new(key)

        return cipher.decrypt(data).rstrip()

def getKeyLength():
    return 32
