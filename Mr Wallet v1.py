import os
import qrcode
import hashlib
import base58
from mnemonic import Mnemonic
from bip32utils import BIP32Key
from eth_account import Account
import ecdsa
from ecdsa import SECP256k1

# Configuración de redes actualizada
NETWORKS = {
    'Bitcoin': {
        'path': "m/44'/0'/0'/0/0",
        'type': 'BTC',
        'key_format': 'WIF'
    },
    'Ethereum': {
        'path': "m/44'/60'/0'/0/0",
        'type': 'ETH',
        'key_format': 'HEX'
    },
    'BNB Smart Chain': {
        'path': "m/44'/9006'/0'/0/0",
        'type': 'BSC',
        'key_format': 'HEX'
    },
    'Polygon': {
        'path': "m/44'/966'/0'/0/0",
        'type': 'MATIC',
        'key_format': 'HEX'
    },
    'TRON': {
        'path': "m/44'/195'/0'/0/0",
        'type': 'TRX',
        'key_format': 'HEX'
    },
    'Avalanche': {
        'path': "m/44'/9000'/0'/0/0",
        'type': 'AVAX',
        'key_format': 'HEX'
    },
    'Fantom': {
        'path': "m/44'/1007'/0'/0/0",
        'type': 'FTM',
        'key_format': 'HEX'
    },
    'Arbitrum': {
        'path': "m/44'/9001'/0'/0/0",
        'type': 'ARB',
        'key_format': 'HEX'
    }
}

# Generar frase semilla BIP39
mnemo = Mnemonic("english")
words = mnemo.generate(strength=256)
seed = mnemo.to_seed(words)

# Función de derivación mejorada
def derive_from_path(root_key, path):
    key = root_key
    for part in path.split('/')[1:]:
        if part.endswith("'"):
            index = int(part[:-1]) + 0x80000000
        else:
            index = int(part)
        key = key.ChildKey(index)
    return key

# Inicializar clave raíz
root_key = BIP32Key.fromEntropy(seed)

# Función para formatear claves privadas
def format_private_key(key, network_type):
    if network_type == 'BTC':
        return key.WalletImportFormat()
    else:
        return '0x' + key.PrivateKey().hex()

# Función para dirección Bitcoin
def btc_address(public_key_hex):
    public_key = bytes.fromhex(public_key_hex)
    sha256 = hashlib.sha256(public_key).digest()
    ripemd160 = hashlib.new('ripemd160', sha256).digest()
    extended = b'\x00' + ripemd160
    checksum = hashlib.sha256(hashlib.sha256(extended).digest()).digest()[:4]
    return base58.b58encode(extended + checksum).decode()

# Función para dirección TRON corregida
def tron_address(private_key_hex):
    private_key = bytes.fromhex(private_key_hex[2:])  # Eliminar el 0x
    sk = ecdsa.SigningKey.from_string(private_key, curve=SECP256k1)
    vk = sk.get_verifying_key()
    public_key = b'\x04' + vk.to_string()
    keccak = hashlib.sha3_256(public_key).digest()
    address_body = keccak[-20:]
    address = b'\x41' + address_body
    checksum = hashlib.sha256(hashlib.sha256(address).digest()).digest()[:4]
    return base58.b58encode(address + checksum).decode()

# Generar wallets para todas las redes
wallets = []
for network, config in NETWORKS.items():
    key = derive_from_path(root_key, config['path'])
    private_key = format_private_key(key, config['type'])
    
    if config['type'] == 'BTC':
        address = btc_address(key.PublicKey().hex())
    elif config['type'] == 'TRX':
        address = tron_address(private_key)
    else:  # Para redes EVM
        account = Account.from_key(private_key)
        address = account.address
    
    wallets.append({
        'network': network,
        'private_key': private_key,
        'address': address
    })

# Generar QR Codes
def generate_qr(data, filename):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)

for wallet in wallets:
    generate_qr(wallet['address'], f"{wallet['network']}_address.png")

# Mostrar resultados
print(f"\n{'='*60}")
print("Frase Semilla (24 palabras):")
print(f"\n{words}\n")
print(f"{'='*60}\n")

for wallet in wallets:
    print(f"Red: {wallet['network']}")
    print(f"Clave Privada: {wallet['private_key']}")
    print(f"Dirección: {wallet['address']}")
    print("-"*60)

print(f"\n{'='*60}")
print("QR Codes generados para todas las direcciones")
print(f"{'='*60}")

# Intentar abrir QRs automáticamente
for wallet in wallets:
    try:
        if os.name == 'nt':
            os.startfile(f"{wallet['network']}_address.png")
        else:
            os.system(f"xdg-open {wallet['network']}_address.png")
    except Exception as e:
        print(f"Error al abrir QR: {str(e)}")