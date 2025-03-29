from locust import HttpUser, task, between
import random
import string

BASE_EMAIL = "loadtest@example.com"
PASSWORD = "password123"

class ShortenerUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.register_and_login()

    def register_and_login(self):
        email = f"{random.randint(1000, 9999)}_{BASE_EMAIL}"
        self.client.post("/auth/register", json={
            "email": email,
            "password": PASSWORD
        })
        login_resp = self.client.post("/auth/login", data={
            "username": email,
            "password": PASSWORD
        })
        token = login_resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {token}"}

    @task(3)
    def create_link(self):
        url = f"https://example.com/{self.random_string()}"
        self.client.post("/links/shorten", json={"original_url": url}, headers=self.headers)

    @task(1)
    def get_expired(self):
        self.client.get("/links/expired", headers=self.headers)

    def random_string(self, length=6):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))