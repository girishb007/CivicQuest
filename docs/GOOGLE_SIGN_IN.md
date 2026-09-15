# Google sign-in setup

The Google button is always shown on Profile. A real OAuth redirect is enabled only when both server credentials are present; local demo identities remain visibly synthetic.

1. Create a **Web application** OAuth client in Google Cloud.
2. Add this exact authorized redirect URI:

   `http://localhost:3000/api/v1/auth/google/callback`

3. Copy `.env.example` to `.env` and set:

   ```text
   CQ_GOOGLE_CLIENT_ID=your-client-id
   CQ_GOOGLE_CLIENT_SECRET=your-client-secret
   ```

4. Restart the API and open Profile. `GET /api/v1/config` should return `google.enabled: true` and the same callback URL.

For a deployed environment, set `CQ_ORIGIN` to the HTTPS application origin and register `<CQ_ORIGIN>/api/v1/auth/google/callback`. Never use demo identities as evidence that live Google OAuth works.
