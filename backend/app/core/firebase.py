"""Inicialización de Firebase Admin SDK y del cliente de Firestore."""

import os
from functools import lru_cache

import firebase_admin
from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore

from app.core.config import get_settings


@lru_cache
def init_firebase() -> firebase_admin.App:
    settings = get_settings()
    if settings.auth_emulator_host:
        # El SDK detecta el emulador mediante esta variable estándar.
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = settings.auth_emulator_host
    if settings.firestore_emulator_host:
        os.environ["FIRESTORE_EMULATOR_HOST"] = settings.firestore_emulator_host
    # Sin emuladores, las credenciales se obtienen de Application Default Credentials
    # (variable GOOGLE_APPLICATION_CREDENTIALS o la cuenta de servicio de Cloud Run).
    return firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})


@lru_cache
def get_db() -> firestore.Client:
    settings = get_settings()
    init_firebase()
    if settings.firestore_emulator_host:
        # El emulador no valida credenciales; Admin SDK igual las exige, por eso se pasan anónimas.
        return firestore.Client(project=settings.firebase_project_id, credentials=AnonymousCredentials())
    return firestore.Client(project=settings.firebase_project_id)
