import requests

class MALClient:
    """
    Represents a client for interacting with the My Anime List API.
    """
    def __init__(
            self,
            client_id: str,
            base_url: str
        ):
        """
        Initializes a MALClient instance.
        Initializes authentication headers for requests to the MAL API.. 
        """
        self.client_id = client_id
        self.base_url = base_url

        self.headers = {
            "X-MAL-CLIENT-ID": self.client_id
        }

    def get_seasonal_anime(
            self,
            year: int,
            season: str
        ) -> requests.Response:
        """
        Gets and returns a response from MAL's seasonal anime endpoint for a given year and season.

        year: an integer e.g., 2009, 2021
        season: "winter", "spring", "summer", "fall"
        """
        endpoint = self.base_url + f"/season/{year}/{season}"
        response = requests.get(endpoint, headers=self.headers)
        return response
        
    def get_rankings(
            self,
            ranking_type: str,
            limit: int
        ) -> requests.Response:
        """
        Gets and returns a response from MAL's ranking endpoint.

        ranking_type: the type of ranking requested(all, airing, etc)
        limit: the number of anime to return (limit of 500)
        """
        endpoint = self.base_url + f"/ranking?ranking_type={ranking_type}&limit={limit}"
        response = requests.get(endpoint, headers=self.headers)
        return response
