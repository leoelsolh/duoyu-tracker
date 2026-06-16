import base64
import json
from hashlib import sha256
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import unpad


def aes_decode(blob_b64, passphrase):
    try:
        blob = base64.b64decode(blob_b64)
        iv, ct = blob[AES.block_size], blob[AES.block_size]
        pass_bytes = passphrase.encode('utf-8') if isinstance(passphrase, str) else passphrase
        key = sha256(pass_bytes).digest()
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ct), AES.block_size)

    except ValueError as e: 
        raise ValueError(f"could not decrypt: {e}")


def rsa_decrypt(ct_b64, pem_key):
    cipher = PKCS1_v1_5.new(RSA.import_key(pem_key))
    return cipher.decrypt(base64.b64decode(ct_b64), None)


def load_config(data, verbose=False):
    private_pem = aes_decode(data['s'], data['k']).decode('utf-8')

    if verbose:
        print("== Extracted private RSA key (preview) ==")
        print(private_pem[:200] + "...\n")

    aes_key = rsa_decrypt(data['k'], private_pem)

    if verbose:
        print(f"== AES key (hex) ==\n{aes_key.hex()}\n")

    plaintext = aes_decode(data['d'], aes_key).decode('utf-8')

    return json.loads(plaintext)

if __name__ == '__main__':

    with open('getapp_response.json') as f:
        response = json.load(f)

    config = load_config(response['data'])

    print("== Decrypted config ==")
    print(json.dumps(config, indent=2, ensure_ascii=False))