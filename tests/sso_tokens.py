# Generate TOKEN using website like https://token.dev/
# Copy new public and private keys in tests/settings.py

# Datetime constants for freezegun in tests
# All SSO tokens (USER1, USER4, RH_EMPLOYEE) expire at: 1781681817 (2025-06-17 07:43:37)
SSO_TOKENS_VALID_DATETIME = "2025-06-17 07:41:38"  # Before token expiration
SSO_TOKENS_EXPIRED_DATETIME = "2029-08-17 19:23:37"  # After token expiration

_doc_access_token_user1 = """
{
  "alg": "RS256",
  "typ": "JWT"
}
{
  "jti": "d485ceb4-4d5a-4b07-888f-f933486ace15",
  "exp": 1781681817,
  "nbf": 0,
  "iat": 1750145817,
  "iss": "http://localhost:8180/auth/realms/redhat-external",
  "aud": [
    "api.dci",
    "account"
  ],
  "sub": "3272474d-a083-4e37-9426-867aa6a46ed6",
  "typ": "Bearer",
  "azp": "dci",
  "auth_time": 0,
  "session_state": "b774d7ea-2c32-44a7-91a8-1b7c8ff98706",
  "acr": "1",
  "allowed-origins": [
    "http://localhost:8000"
  ],
  "realm_access": {
    "roles": [
      "uma_authorization"
    ]
  },
  "resource_access": {
    "account": {
      "roles": [
        "manage-account",
        "manage-account-links",
        "view-profile"
      ]
    }
  },
  "email": "user1@example.org",
  "username": "user1"
}
"""

ACCESS_TOKEN_USER1 = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkNDg1Y2ViNC00ZDVhLTRiMDctODg4Zi1mOTMzNDg2YWNlMTUiLCJleHAiOjE3ODE2ODE4MTcsIm5iZiI6MCwiaWF0IjoxNzUwMTQ1ODE3LCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAvYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjpbImFwaS5kY2kiLCJhY2NvdW50Il0sInN1YiI6IjMyNzI0NzRkLWEwODMtNGUzNy05NDI2LTg2N2FhNmE0NmVkNiIsInR5cCI6IkJlYXJlciIsImF6cCI6ImRjaSIsImF1dGhfdGltZSI6MCwic2Vzc2lvbl9zdGF0ZSI6ImI3NzRkN2VhLTJjMzItNDRhNy05MWE4LTFiN2M4ZmY5ODcwNiIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cDovL2xvY2FsaG9zdDo4MDAwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sImVtYWlsIjoidXNlcjFAZXhhbXBsZS5vcmciLCJ1c2VybmFtZSI6InVzZXIxIn0.GfMVb_0G2Yjvr0ybFFCYiABWpdF7HcYdqHf7pLxlawLf3R2JgbJ0ZzrkB7NVQ1-iUoeFRxcnzSi0wu0x1HS16VIgwSQPMed3SAo33tUcvRWpdD1FTop5WYe6m1Z3hIImM2odiTzUMO-scfxdnjfOCpFH51DnT9ZsBylmBV4M9t6invW7uMcHr7r2MunlgvN6YhZ8KKNrJvVV1amKATwq8cSY0w3mTAuY6mTDVU1M7dvJvOuNLhnTV6IzwNS4wpwkOR2LGdXC0jwY8vS4edwI_ItC8qsbqEujcyjm07QlknhHNz0rRTPrCd88NAbq3opwKqIPrac85VEkg2x9W80hNg"

_doc_access_token_user4 = """
{
  "alg": "RS256",
  "typ": "JWT"
}
{
  "jti": "d485ceb4-4d5a-4b07-888f-f933486ace15",
  "exp": 1781681817,
  "nbf": 0,
  "iat": 1750145817,
  "iss": "http://localhost:8180/auth/realms/redhat-external",
  "aud": [
    "api.dci",
    "account"
  ],
  "sub": "3272474d-a083-4e37-9426-867aa6a46ed6",
  "typ": "Bearer",
  "azp": "dci",
  "auth_time": 0,
  "session_state": "b774d7ea-2c32-44a7-91a8-1b7c8ff98706",
  "acr": "1",
  "allowed-origins": [
    "http://localhost:8000"
  ],
  "realm_access": {
    "roles": [
      "uma_authorization"
    ]
  },
  "resource_access": {
    "account": {
      "roles": [
        "manage-account",
        "manage-account-links",
        "view-profile"
      ]
    }
  },
  "email": "user4@example.org",
  "username": "user4"
}
"""

ACCESS_TOKEN_USER4 = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkNDg1Y2ViNC00ZDVhLTRiMDctODg4Zi1mOTMzNDg2YWNlMTUiLCJleHAiOjE3ODE2ODE4MTcsIm5iZiI6MCwiaWF0IjoxNzUwMTQ1ODE3LCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAvYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjpbImFwaS5kY2kiLCJhY2NvdW50Il0sInN1YiI6IjMyNzI0NzRkLWEwODMtNGUzNy05NDI2LTg2N2FhNmE0NmVkNiIsInR5cCI6IkJlYXJlciIsImF6cCI6ImRjaSIsImF1dGhfdGltZSI6MCwic2Vzc2lvbl9zdGF0ZSI6ImI3NzRkN2VhLTJjMzItNDRhNy05MWE4LTFiN2M4ZmY5ODcwNiIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cDovL2xvY2FsaG9zdDo4MDAwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sImVtYWlsIjoidXNlcjRAZXhhbXBsZS5vcmciLCJ1c2VybmFtZSI6InVzZXI0In0.NGFxyx5SHGR3CBbgEuG2iOAr0HQn0nV4h41r7TZ6x_d87oJ92Y4on1HYLEnr0KaWFkPKGNk2VW4XXyr8iTcB5DFlmTnC_EgJYU5OeB3luhHis38kgFcP0PnJJ3whyZ_uzVutdPWjf_KECukSMzYFhEGwRJe0xSIQ-1FSL7UI8z_JUpe2Y0auVQ8Yjq9llhtaadzEbPO6fn2LGy-M_QVpv2U7rx0sVJ76s66b90qbdPWZyKXfAgyfm-IVBpmaPNaQJJVwu5Qa9OmwNebmFcYPatdbuP5eUFeJdlLDXB6ZpoCqfgQWueCzUeLDnT554xlbaEUYtciniBRgBIDn2t5SKg"

_doc_access_token_rh_employee = """
{
  "alg": "RS256",
  "typ": "JWT"
}
{
  "jti": "9717d8b3-73d9-4b6e-be8f-fc9fe9a24454",
  "exp": 1781681817,
  "nbf": 0,
  "iat": 1750145817,
  "iss": "http://localhost:8180/auth/realms/redhat-external",
  "aud": [
    "api.dci",
    "account"
  ],
  "sub": "ddf4ce78-6682-4df2-bbbc-f2e61fe576e0",
  "typ": "Bearer",
  "azp": "dci",
  "auth_time": 0,
  "session_state": "85ae77a0-87eb-4c5d-938e-90f251a2071e",
  "acr": "1",
  "allowed-origins": [
    "http://localhost:8000"
  ],
  "realm_access": {
    "roles": [
      "redhat:employees",
      "uma_authorization"
    ]
  },
  "resource_access": {
    "account": {
      "roles": [
        "manage-account",
        "manage-account-links",
        "view-profile"
      ]
    }
  },
  "email": "rh_employee@redhat.com",
  "username": "rh_employee"
}
"""

ACCESS_TOKEN_RH_EMPLOYEE = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI5NzE3ZDhiMy03M2Q5LTRiNmUtYmU4Zi1mYzlmZTlhMjQ0NTQiLCJleHAiOjE3ODE2ODE4MTcsIm5iZiI6MCwiaWF0IjoxNzUwMTQ1ODE3LCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAvYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjpbImFwaS5kY2kiLCJhY2NvdW50Il0sInN1YiI6ImRkZjRjZTc4LTY2ODItNGRmMi1iYmJjLWYyZTYxZmU1NzZlMCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImRjaSIsImF1dGhfdGltZSI6MCwic2Vzc2lvbl9zdGF0ZSI6Ijg1YWU3N2EwLTg3ZWItNGM1ZC05MzhlLTkwZjI1MWEyMDcxZSIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cDovL2xvY2FsaG9zdDo4MDAwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJyZWRoYXQ6ZW1wbG95ZWVzIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJlbWFpbCI6InJoX2VtcGxveWVlQHJlZGhhdC5jb20iLCJ1c2VybmFtZSI6InJoX2VtcGxveWVlIn0.dU9oF0ukQ3m1PIAcjlVyOoZVRTmJU_fZDN5-rMvESx2P1eFdI22kjx30-QQmLYFk2fFMkN74TWlFxf8d5w-4xc_FK5DQkWj7-OoCTOOBelR82-9ufa2GLZC5Fy_GKOo_qklh6_MpAEjaq6dPzJQqOn8jLNBjOY5B77oAg_iDWK38ThnJ0GX-7aO2a9gRN0PWWh2euRsrP3PTnzk91tWspZonKEwgRtn45FGrWe0UcJW3m-zFGzRYfEemLQLcApxZ-5ZTYhQSF7pkvNgbO2wTBAA3nKXQkBYsYkHEHHbQnobOtDlC7-cbeNEw5qk3QWZrjTQmMsBbBvf2Ry1Re_dL9A"
