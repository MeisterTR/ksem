"""Hilfsfunktionen für KSEM Component"""

def bearer_header(access_token: str) -> dict:
    """Erzeugt Header für Bearer-Token-Authentifizierung"""
    return {"Authorization": f"Bearer {access_token}"}
