import google.auth
import google.auth.transport.requests
import google.oauth2.id_token

def get_id_token(target_audience: str) -> str:
    """
    Returns an ID token used to call a private Cloud Run service.
    `target_audience` should be the base URL of the GROBID service, e.g.
    'https://grobid-service-xxxx-uc.a.run.app'.
    """
    creds, _ = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    token = google.oauth2.id_token.fetch_id_token(auth_req, target_audience)
    return token

