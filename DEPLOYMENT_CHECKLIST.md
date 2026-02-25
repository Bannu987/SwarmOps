# SwarmOps Deployment Checklist

Before deploying the frontend to Vercel and the backend to Railway (or Render), you must configure the environment variables in both hosting platforms. This checklist ensures you don't miss any critical keys that could cause agents or integrations to fail.

## 🟢 1. Vercel (Frontend Provider)
Go to your project settings in Vercel > Environment Variables and add the following:

- [ ] `REACT_APP_API_URL` (or `NEXT_PUBLIC_API_URL`)
  - **Value**: The live HTTPS URL of your deployed Railway backend. (e.g., `https://swarmops-backend-production.up.railway.app`)
  - **Why**: Allows your React frontend to connect to the deployed backend instead of attempting to hit `http://localhost:8000`.

---

## 🔵 2. Railway / Render (Backend Provider)
Go to your project variables in Railway/Render and add your API keys. You can refer to your local `.env` file for your existing keys. 

### Core AI Providers (Required)
- [ ] `GROQ_API_KEY` - Required for fast reasoning (Llama 3).
- [ ] `GEMINI_API_KEY` - Required for standard capabilities.

### Multi-Provider Routing (Required)
- [ ] `OPENROUTER_API_KEY` - Required if your Nexus model router falls back to OpenRouter models.
- [ ] `NVIDIA_API_KEY` - Required for Nvidia NIM models.
- [ ] `SERPER_API_KEY` - Required for the Deep Research + SEO Agent's Google Search capabilities.

### Additional Providers (Optional based on usage)
- [ ] `DEEPSEEK_API_KEY` - Required if you use DeepSeek models for coding or complex logic.
- [ ] `BRAVE_API_KEY` - Optional secondary research provider (Deep Research Agent uses this).

### Google Cloud Configs (Optional)
- [ ] `GOOGLE_SERVICE_ACCOUNT_JSON` - Needed for Google Analytics 4 integration. (Path or json string depending on your setup).
- [ ] `GA4_PROPERTY_ID` - Required to pull live Analytics Agent data.
- [ ] `SEARCH_CONSOLE_SITE_URL` - Required for SEO Agent rankings validation.
- [ ] `GOOGLE_ADS_CUSTOMER_ID` - Required for PPC Agent performance pulling.
- [ ] `GOOGLE_ADS_DEVELOPER_TOKEN` - Required for PPC Agent optimization and campaign creation.

### Integrations (Optional)
- [ ] `HUBSPOT_ACCESS_TOKEN` - Required for CRM Agent.
- [ ] `DATAFORSEO_LOGIN` & `DATAFORSEO_PASSWORD` - Required for real SEO keyword data.
- [ ] `WORDPRESS_URL`, `WORDPRESS_USERNAME`, `WORDPRESS_APP_PASSWORD` - Required for Content Agent remote publishing.

### Server Config (Optional)
- [ ] `PORT` - Railway/Render automatically injects this. You usually **do not** need to set this manually unless requested by the platform.
