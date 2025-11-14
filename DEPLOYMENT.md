# Vercel Deployment Guide

This guide will help you deploy the Middleman AI Flask application to Vercel.

## Prerequisites

1. A Vercel account (sign up at https://vercel.com)
2. Vercel CLI installed (optional, for local testing):
   ```bash
   npm i -g vercel
   ```

## Environment Variables

Before deploying, make sure to set the following environment variables in your Vercel project settings:

### Required Environment Variables:

1. **SUPABASE_URL** - Your Supabase project URL
2. **SUPABASE_KEY** - Your Supabase anon/service role key
3. **MISTRAL_API_KEY** - Your Mistral AI API key
4. **SECRET_KEY** - A secret key for Flask sessions (generate a random string)
5. **LOGIN_USERNAME** - Username for UI login
6. **LOGIN_PASSWORD** - Password for UI login
7. **API_KEY** - API key for API endpoints (X-API-Key header)

### Optional Environment Variables:

- **FLASK_ENV** - Set to `production` for production deployment
- **PORT** - Port number (Vercel handles this automatically)

## Deployment Steps

### Option 1: Deploy via Vercel Dashboard

1. **Push your code to GitHub/GitLab/Bitbucket**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Import project in Vercel**
   - Go to https://vercel.com/new
   - Import your Git repository
   - Vercel will auto-detect the Python project

3. **Configure environment variables**
   - In the project settings, go to "Environment Variables"
   - Add all required environment variables listed above

4. **Deploy**
   - Click "Deploy"
   - Wait for the build to complete

### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   vercel
   ```

4. **Set environment variables**:
   ```bash
   vercel env add SUPABASE_URL
   vercel env add SUPABASE_KEY
   vercel env add MISTRAL_API_KEY
   vercel env add SECRET_KEY
   vercel env add LOGIN_USERNAME
   vercel env add LOGIN_PASSWORD
   vercel env add API_KEY
   ```

5. **Deploy to production**:
   ```bash
   vercel --prod
   ```

## Project Structure

The deployment uses the following structure:

```
middleman_ai/
├── api/
│   └── index.py          # Vercel serverless function entry point
├── app.py                 # Main Flask application
├── vercel.json            # Vercel configuration
├── requirements.txt       # Python dependencies
├── .vercelignore         # Files to exclude from deployment
└── ...                    # Other project files
```

## Important Notes

1. **Static Files**: Vercel will serve static files from the `static/` folder automatically
2. **Templates**: Flask templates in `templates/` will be included in the deployment
3. **Session Storage**: Flask sessions use server-side storage. For production, consider using a session store like Redis
4. **File Uploads**: If you plan to add file upload functionality, use Vercel Blob Storage or an external service
5. **Cold Starts**: Serverless functions may experience cold starts. Consider using Vercel Pro for better performance

## Troubleshooting

### Build Errors

If you encounter build errors:

1. Check that all dependencies in `requirements.txt` are compatible
2. Ensure Python version is compatible (Vercel uses Python 3.9+)
3. Check Vercel build logs for specific error messages

### Runtime Errors

If the app runs but has errors:

1. Verify all environment variables are set correctly
2. Check that Supabase credentials are valid
3. Ensure Mistral API key is valid
4. Check Vercel function logs in the dashboard

### Static Files Not Loading

If static files (CSS, JS) aren't loading:

1. Verify the `static/` folder structure
2. Check that file paths in HTML are correct
3. Ensure `static_folder='static'` is set in Flask app initialization

## Testing Locally

You can test the Vercel deployment locally:

```bash
vercel dev
```

This will start a local server that mimics Vercel's serverless environment.

## Production Checklist

- [ ] All environment variables are set
- [ ] SECRET_KEY is a strong random string
- [ ] LOGIN_PASSWORD is strong
- [ ] API_KEY is strong and secure
- [ ] FLASK_ENV is set to `production`
- [ ] All dependencies are in `requirements.txt`
- [ ] No sensitive data in code
- [ ] CORS is configured correctly (if needed)
- [ ] Error handling is in place
- [ ] Health check endpoint is working

## Support

For Vercel-specific issues, refer to:
- [Vercel Python Documentation](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- [Vercel Support](https://vercel.com/support)

