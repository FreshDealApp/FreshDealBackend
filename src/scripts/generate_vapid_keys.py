import os
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# Generate a new ECDSA key pair
private_key = ec.generate_private_key(ec.SECP256R1())

# Get the private key in PEM format
pem_private = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Get the public key in PEM format
public_key = private_key.public_key()
pem_public = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Convert to the format expected by pywebpush
private_key_str = pem_private.decode('utf-8')
private_key_str = private_key_str.replace('-----BEGIN PRIVATE KEY-----\n', '')
private_key_str = private_key_str.replace('\n-----END PRIVATE KEY-----\n', '')

public_key_str = pem_public.decode('utf-8')
public_key_str = public_key_str.replace('-----BEGIN PUBLIC KEY-----\n', '')
public_key_str = public_key_str.replace('\n-----END PUBLIC KEY-----\n', '')

print("VAPID_PRIVATE_KEY =", private_key_str)
print("VAPID_PUBLIC_KEY =", public_key_str)