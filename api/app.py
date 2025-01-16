import logging
import random
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt, jwk
import requests


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
SECRET = os.getenv("CLIENT_SECRET")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")

PUBLIC_KEY_URL = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
ISSUER = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"


oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{ISSUER}/protocol/openid-connect/auth",
    tokenUrl=f"{ISSUER}/protocol/openid-connect/token"
)


app = FastAPI()

origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_public_key():
    response = requests.get(PUBLIC_KEY_URL)
    if response.status_code != 200:
        logger.error(f"Error: {response.status_code}, {response.text}")
        response.raise_for_status()
    jwks = response.json()
    keycloak_rsa_key = {}
    for key in jwks['keys']:
        if key['kty'] == 'RSA' and key['use'] == 'sig' and key['alg'] == 'RS256':
            keycloak_rsa_key = key
            break
    if not keycloak_rsa_key:
        raise ValueError("RSA key not found in Keycloak JWKS")
    return jwk.construct(keycloak_rsa_key)


public_key = get_public_key()
logger.info(f"Публичный ключ: {public_key}")

def verify_token(token: str):
    try:
        header = jwt.get_unverified_header(token)
        kid = header['kid']
        key = public_key
        payload = jwt.decode(token, key, algorithms=["RS256"], audience=CLIENT_ID)
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e


def check_user_role(payload: dict):
    user_role = payload['realm_access']['roles'][0]
    if user_role != 'prothetic_user':
        raise HTTPException(status_code=403, detail="Forbidden")
    return True


async def get_download_access(token: str = Depends(oauth2_scheme)):
    return check_user_role(verify_token(token))


@app.get("/reports")
async def get_report(download_access: bool = Depends(get_download_access)):
    if download_access:
        random_data = {
            "id": random.randint(1, 1000),
            "value": random.uniform(0.1, 99.9),
            "description": "This is some random data"
        }
        with open('report.txt', mode='w') as file:
            file.write(str(random_data))
        return FileResponse('report.txt', media_type="application/txt", filename="report.txt")
