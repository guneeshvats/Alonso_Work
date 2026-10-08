from locust import HttpUser, task, between
import json

class SearchUser(HttpUser):
    wait_time = between(1, 3)
    token = None
    payloads = []

    def on_start(self):
        # Authenticate with form data
        auth_response = self.client.post(
            "/auth/login",
            data={
                "grant_type": "password",
                "username": "AlabamaUser",
                "password": "Password123",
                "scope": "",
                "client_id": "string",
                "client_secret": "string"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print("Auth response:", auth_response.status_code, auth_response.text)
        if auth_response.status_code == 200:
            self.token = auth_response.json().get("access_token")  # FastAPI usually returns access_token
            print("Authenticated successfully, token:", self.token)
        else:
            print(f"Authentication failed [{auth_response.status_code}]: {auth_response.text}")

            # Load payloads
        with open("requests.json", "r") as f:
            self.payloads = json.load(f)
        if not self.payloads:
            print("No payloads loaded!")

    @task
    def search(self):
        if not self.token:
            print("No token, skipping search task.")
            return
        if not self.payloads:
            print("No payloads, skipping search task.")
            return

        request_template = {
          "BasicQuery": "Passing Completions",
          "SportCode": "MFB",
          "TeamCode": "31",
          "Entity": "Player",
          "TimePeriod": "Game",
          "GamePeriod": "All Quarters",
          "PageNumber": 1,
          "PageSize": 10,
          "AQLOnly": False,
        }

        # Pick a random payload
        import random
        payload = random.choice(self.payloads)

        request_template["aql_output"] = payload["aql"]
        request_template["BasicQuery"] = payload["query"]
        #request_template["Entity"] = payload["entity"]

        print(json.dumps(request_template, indent=4))

        # Make the authenticated request
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.post("/api/search", json=request_template, headers=headers)

        if response.status_code != 200:
            print("Search failed:", response.text)


        print(response.text)
