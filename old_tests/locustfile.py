import random
import uuid
from locust import HttpUser, task, between
import logging

# Configuration matching docker-compose.txt ports
USER_SERVICE_URL = "http://localhost:8000"
LP_SERVICE_URL = "http://localhost:8002"
EVENT_SERVICE_URL = "http://localhost:8003"


class AdaptiveLearningUser(HttpUser):
    # Simulate realistic think time between actions (Section 9: Time steps t)
    wait_time = between(1, 5)

    def on_start(self):
        """
        Simulates the "Initialization" phase (t=0).
        Registers and logs in to get a JWT token.
        """
        self.email = f"student_{uuid.uuid4()}@example.com"
        self.password = "secure_password_123"
        self.first_name = "Test"
        self.last_name = "User"
        self.user_id = None
        self.token = None

        # 1. Register (User Service)
        # Note: We point self.client to the primary service usually,
        # but here we assume a gateway or absolute URLs for microservices.
        with self.client.post(
            f"{USER_SERVICE_URL}/api/v1/auth/register",
            json={
                "email": self.email,
                "password": self.password,
                "first_name": self.first_name,
                "last_name": self.last_name,
            },
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(f"Registration failed: {response.text}")
                return

        # 2. Login to get Token
        response = self.client.post(
            f"{USER_SERVICE_URL}/api/v1/auth/login", json={"email": self.email, "password": self.password}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            # Decode token to get ID (simplified for test)
            # In real test, fetch /me/profile
            profile_resp = self.client.get(
                f"{USER_SERVICE_URL}/api/v1/users/me/profile", headers={"Authorization": f"Bearer {self.token}"}
            )
            self.user_id = str(profile_resp.json()["id"])
        else:
            logging.error(f"Login failed: {response.text}")

    @task(weight=1)
    def generate_learning_path(self):
        """
        Critical Path: Heavy Calculation.
        Chains: User -> LP -> KG (A*) + ML (Mastery)
        Success Criteria: < 3 seconds
        """
        if not self.token or not self.user_id:
            return

        # Goal Concept ID (taken from seed data in ml_service.txt)
        GOAL_CONCEPT = "77bea151-fe78-5e8b-99a6-1446a27d32f6"  # OOP

        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "start_concept_id": None,  # Force 'root' search (heavier)
            "goal_concept_id": GOAL_CONCEPT,
        }

        self.client.post(
            f"{LP_SERVICE_URL}/api/v1/students/{self.user_id}/learning-paths",
            json=payload,
            headers=headers,
            name="Generate Path (A* + DKT)",
        )

    @task(weight=5)
    def get_recommendations(self):
        """
        Real-time Adaptive Loop.
        Chains: LP -> ML (RL Inference)
        Success Criteria: < 200 ms
        """
        if not self.token or not self.user_id:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get(
            f"{LP_SERVICE_URL}/api/v1/students/{self.user_id}/recommendations",
            headers=headers,
            name="Get RL Recommendations",
        )

    @task(weight=10)
    def send_learning_event(self):
        """
        High Throughput Ingestion.
        Chains: Event Service -> MongoDB (via Celery)
        """
        if not self.user_id:
            return

        payload = {
            "event_type": "VIDEO_PLAY",
            "student_id": self.user_id,
            "metadata": {"duration": random.randint(10, 300)},
        }

        # Event service is usually fire-and-forget
        self.client.post(f"{EVENT_SERVICE_URL}/api/v1/events", json=payload, name="Ingest Event")
