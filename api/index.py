from app.main import app

# Vercel serverless function handler
async def handler(request):
    return await app(request)
