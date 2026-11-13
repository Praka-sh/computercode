import asyncio
import sys
import unittest
from httpx import AsyncClient

# Add app to path
sys.path.insert(0, '.')

from app.main import app

class TestHealth(unittest.TestCase):
    def test_health_sync(self):
        async def run_test():
            async with AsyncClient(app=app, base_url="http://test") as client:
                res = await client.get("/health")
                self.assertEqual(res.status_code, 200)
                self.assertEqual(res.json()["status"], "healthy")

                res_api = await client.get("/api/v1/health")
                self.assertEqual(res_api.status_code, 200)
                self.assertEqual(res_api.json()["status"], "healthy")

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()