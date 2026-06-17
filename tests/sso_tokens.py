# Generate TOKEN using website like https://token.dev/
# Copy new public and private keys in tests/settings.py

# Datetime constants for freezegun in tests
# All SSO tokens (USER1, USER4, RH_EMPLOYEE) issued at: 1781712000 (2026-06-17 16:00:00 UTC), expire at: 1813248000 (2027-06-17 16:00:00 UTC)
SSO_TOKENS_VALID_DATETIME = "2026-06-17 17:00:00"  # Before token expiration
SSO_TOKENS_EXPIRED_DATETIME = "2027-06-18 17:00:00"  # After token expiration

_doc_access_token_user1 = """
{
  "alg": "RS256",
  "typ": "JWT"
}
{
  "jti": "d485ceb4-4d5a-4b07-888f-f933486ace15",
  "exp": 1813248000,
  "nbf": 0,
  "iat": 1781712000,
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

ACCESS_TOKEN_USER1 = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkNDg1Y2ViNC00ZDVhLTRiMDctODg4Zi1mOTMzNDg2YWNlMTUiLCJleHAiOjE4MTMyNDgwMDAsIm5iZiI6MCwiaWF0IjoxNzgxNzEyMDAwLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAvYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjpbImFwaS5kY2kiLCJhY2NvdW50Il0sInN1YiI6IjMyNzI0NzRkLWEwODMtNGUzNy05NDI2LTg2N2FhNmE0NmVkNiIsInR5cCI6IkJlYXJlciIsImF6cCI6ImRjaSIsImF1dGhfdGltZSI6MCwic2Vzc2lvbl9zdGF0ZSI6ImI3NzRkN2VhLTJjMzItNDRhNy05MWE4LTFiN2M4ZmY5ODcwNiIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cDovL2xvY2FsaG9zdDo4MDAwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sImVtYWlsIjoidXNlcjFAZXhhbXBsZS5vcmciLCJ1c2VybmFtZSI6InVzZXIxIn0.lCnuAMB1xS350hDImrWWf8CeFvL8dEKD4BdSOPXC_VxkeG8WL6huBZpe0DS8ID0v3nnGOAp2IJTzhm1gTpJaXVfjeNb5A8RttpZKgExMpfginQRVbe_-gKRnuYidKu7fjxAvgT9-oJXP09L6PjqzlsFkgr9KAByp7Vc9y4sZffYqupPK7QPrwLrNS1c2WiM5Fc4hyoUEmlDw2ICq-2gE5LlABh6QcInX9lYo2_bYpy0B1NALMONgPPoyNSULLpMAIRiO6Ge6rKQ2brgF06Ci2Q0-PNyJ4MTHmmOZvGpdJEKyhN8WDDQYB2Z22OpD6OxQtqlRnv70CDE5FuETfJE3QA"

_doc_access_token_user4 = """
{
  "alg": "RS256",
  "typ": "JWT"
}
{
  "jti": "d485ceb4-4d5a-4b07-888f-f933486ace15",
  "exp": 1813248000,
  "nbf": 0,
  "iat": 1781712000,
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

ACCESS_TOKEN_USER4 = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkNDg1Y2ViNC00ZDVhLTRiMDctODg4Zi1mOTMzNDg2YWNlMTUiLCJleHAiOjE4MTMyNDgwMDAsIm5iZiI6MCwiaWF0IjoxNzgxNzEyMDAwLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAvYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjpbImFwaS5kY2kiLCJhY2NvdW50Il0sInN1YiI6IjMyNzI0NzRkLWEwODMtNGUzNy05NDI2LTg2N2FhNmE0NmVkNiIsInR5cCI6IkJlYXJlciIsImF6cCI6ImRjaSIsImF1dGhfdGltZSI6MCwic2Vzc2lvbl9zdGF0ZSI6ImI3NzRkN2VhLTJjMzItNDRhNy05MWE4LTFiN2M4ZmY5ODcwNiIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cDovL2xvY2FsaG9zdDo4MDAwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sImVtYWlsIjoidXNlcjRAZXhhbXBsZS5vcmciLCJ1c2VybmFtZSI6InVzZXI0In0.Nnwq2fYF0tk4PBJsGVCa0zhmL7bwEEILLAfQRnFt2biooHRRhXjg2y_5pLmcTNN-cmOsjwjjoTFj_e73OVBXjT517cI2JTNujMKbWnJ6jxwd3bLG1fw7RZTRQbtqpZAjexohhhQCdNFppebUAArHRQgkwCiDFt2SwLUKQny7ZPCAtOyDdE8t02Mvb7sql3zuYZIc7u7hNh4AhQA7VvNMzoop1gCEzudnSY6VrCc_G30t6zMwOi0g5qrxKBxHaf89KB6QopXQVV__8FoizHcONSyQG0TpQBtRNl1LxidhaSmzQXwtQNC_9pzZQvU8Qo46xFG8jtJyrsLjSGlTIq5nGw"

_doc_access_token_rh_employee = """
{
  "alg": "RS256",
  "typ": "JWT"
}
{
  "jti": "9717d8b3-73d9-4b6e-be8f-fc9fe9a24454",
  "exp": 1813248000,
  "nbf": 0,
  "iat": 1781712000,
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

ACCESS_TOKEN_RH_EMPLOYEE = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI5NzE3ZDhiMy03M2Q5LTRiNmUtYmU4Zi1mYzlmZTlhMjQ0NTQiLCJleHAiOjE4MTMyNDgwMDAsIm5iZiI6MCwiaWF0IjoxNzgxNzEyMDAwLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAvYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjpbImFwaS5kY2kiLCJhY2NvdW50Il0sInN1YiI6ImRkZjRjZTc4LTY2ODItNGRmMi1iYmJjLWYyZTYxZmU1NzZlMCIsInR5cCI6IkJlYXJlciIsImF6cCI6ImRjaSIsImF1dGhfdGltZSI6MCwic2Vzc2lvbl9zdGF0ZSI6Ijg1YWU3N2EwLTg3ZWItNGM1ZC05MzhlLTkwZjI1MWEyMDcxZSIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cDovL2xvY2FsaG9zdDo4MDAwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJyZWRoYXQ6ZW1wbG95ZWVzIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJlbWFpbCI6InJoX2VtcGxveWVlQHJlZGhhdC5jb20iLCJ1c2VybmFtZSI6InJoX2VtcGxveWVlIn0.OAD8CE5BIoXEARO5s9rgzW2-dz4cMvPbqfGbx7Lwca7qXdSymngV8Ddj4dLZf3vnsy4qs7zUZPaGnV_7X_2F3hyI5sc51mt0SQKWidfKUMsUXPMECbp3L22qQiJXwYZSVs5L79RNohsYe2E9RFKOzqy7Lkhy_VPgROW-j27GqU5tUITwH6AoMwf5BN08Cz_HUwSdmHFbhFoIANg9iD9iJo1GHpSj_CEa1ZDqb-NRVkDYwYX0pqdKgfRdlEcmf-LoLfKksDoL9N9SUq0bFC81P_VHRuo5Jua-myKh96HucVy9HfiDqkHol8ugKtXLq-_uD_OhlthOZ9e8f2M2Q6VIbQ"
