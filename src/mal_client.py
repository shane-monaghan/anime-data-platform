import requests

class MAL_Client:
    def __init__(self, client_id, base_url):
        self.client_id = client_id
        self.base_url = base_url

        self.headers = {
            "X-MAL-CLIENT-ID": self.client_id
        }

    def get_seasonal_anime(self, year, season):
        endpoint = self.base_url + f"/season/{year}/{season}"
        response = requests.get(endpoint, headers=self.headers)
        return response