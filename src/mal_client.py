import requests


class MALClient:
    """Client for interacting with the MyAnimeList API."""

    def __init__(self, client_id: str, base_url: str):
        """Initialize a MALClient instance.

        Args:
            client_id: MAL API client ID used for authentication.
            base_url: Base URL for MAL API requests.
        """
        self.client_id = client_id
        self.base_url = base_url

        self.headers = {"X-MAL-CLIENT-ID": self.client_id}

    def get_seasonal_anime(self, year: int, season: str) -> requests.Response:
        """Fetch seasonal anime data from the MyAnimeList API.

        Args:
            year: Year of the seasonal anime listing.
            season: Season name, such as "winter", "spring", "summer", or "fall".

        Returns:
            requests.Response object from the MAL API.
        """
        endpoint = self.base_url + f"/season/{year}/{season}"
        response = requests.get(endpoint, headers=self.headers)
        return response

    def get_rankings(self, ranking_type: str, limit: int) -> requests.Response:
        """Fetch ranking data from the MyAnimeList API.

        Args:
            ranking_type: Type of ranking to request, such as "all" or "airing".
            limit: Maximum number of results to return.

        Returns:
            requests.Response object from the MAL API.
        """
        endpoint = self.base_url + f"/ranking?ranking_type={ranking_type}&limit={limit}"
        response = requests.get(endpoint, headers=self.headers)
        return response
