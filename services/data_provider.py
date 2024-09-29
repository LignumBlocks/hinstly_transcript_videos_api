import requests
from apify_client import ApifyClient
from abc import ABC, abstractmethod

class DataProvider(ABC):
    @abstractmethod
    def fetch_data(self, profile: str, videos_count: int, kv_store_name: str) -> dict:
        pass

# Implementación específica de Apify
class ApifyDataProvider(DataProvider):
    def __init__(self, client, api_token: str):
        self.client = client
        self.api_token = api_token

    def fetch_data(self, profile: str, videos_count: int, kv_store_name: str) -> dict:
        run_input = {
            "profiles": [profile],
            "resultsPerPage": videos_count,
            "excludePinnedPosts": True,
            "shouldDownloadVideos": True,
            "shouldDownloadCovers": False,
            "shouldDownloadSubtitles": False,
            "shouldDownloadSlideshowImages": False,
            "videoKvStoreIdOrName": kv_store_name
        }
        run = self.client.actor("OtzYfK1ndEGdwWFKQ").call(run_input=run_input)

        dataset_id = run["defaultDatasetId"]
        dataset_items = list(self.client.dataset(dataset_id).iterate_items())

        # Buscar el Key Value Store por nombre para obtener los enlaces de descarga
        kv_store_list_url = f"https://api.apify.com/v2/key-value-stores?token={self.api_token}"
        kv_store_list_response = requests.get(kv_store_list_url)

        if kv_store_list_response.status_code == 200:
            response_json = kv_store_list_response.json()

            kv_store_id = None
            for store in response_json.get("data", {}).get("items", []):
                if store["name"] == kv_store_name:
                    kv_store_id = store["id"]
                    break

            if not kv_store_id:
                raise Exception(f"No se encontró el Key Value Store con el nombre {kv_store_name}")

            # Obtener las claves de los videos en el Key Value Store
            kv_store_keys_url = f"https://api.apify.com/v2/key-value-stores/{kv_store_id}/keys?token={self.api_token}"
            kv_store_keys_response = requests.get(kv_store_keys_url)

            if kv_store_keys_response.status_code == 200:
                keys_data = kv_store_keys_response.json()
                videos = keys_data.get("data", {}).get("items", [])

                # Variable para almacenar los resultados
                profile_data = {
                    "profile_id": dataset_items[0].get("authorMeta", {}).get("id"),
                    "profile_name": dataset_items[0].get("authorMeta", {}).get("name"),
                    "videos": []
                }

                # Construimos el JSON con las URLs de TikTok y los enlaces de descarga
                for item, video_key in zip(dataset_items, videos):
                    profile_data["videos"].append({
                        "video_url": item.get("webVideoUrl"),
                        "download_link": f"https://api.apify.com/v2/key-value-stores/{kv_store_id}/records/{video_key['key']}"
                    })

                return profile_data
            else:
                raise Exception(f"Error al obtener las claves de los videos del Key Value Store.")
        else:
            raise Exception("Error al obtener la lista de Key Value Stores.")
