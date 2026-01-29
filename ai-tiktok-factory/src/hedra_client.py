import os
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

class HedraClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": self.api_key})

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=20))
    def list_models(self) -> list[dict]:
        r = self.session.get(self._url("/models"), timeout=60)
        r.raise_for_status()
        return r.json()

    def pick_model_id(self, preferred_names: list[str]) -> str:
        models = self.list_models()
        normalized = [(m.get("id"), (m.get("name") or "").lower()) for m in models]
        for want in preferred_names:
            w = want.lower()
            for mid, nm in normalized:
                if w in nm:
                    return mid
        raise RuntimeError(f"Could not find model containing any of: {preferred_names}. Models returned: {[m.get('name') for m in models]}")

    def create_asset(self, name: str, asset_type: str) -> dict:
        payload = {"name": name, "type": asset_type}
        r = self.session.post(self._url("/assets"), json=payload, timeout=60)
        r.raise_for_status()
        return r.json()

    def upload_asset(self, asset_id: str, file_path: str) -> dict:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            r = self.session.post(self._url(f"/assets/{asset_id}/upload"), files=files, timeout=300)
            r.raise_for_status()
            return r.json()

    def generate_video(self, ai_model_id: str, start_keyframe_id: str, audio_id: str, duration_ms: int, aspect_ratio: str, resolution: str) -> dict:
        payload = {
            "generated_video_inputs": {
                "text_prompt": "TikTok news anchor delivery, crisp studio lighting, subtle head motion, realistic lip sync.",
                "resolution": resolution,
                "aspect_ratio": aspect_ratio,
                "duration_ms": duration_ms,
                "bounding_box_target": {"[0]": 0.5, "[1]": 0.5}
            },
            "type": "video",
            "ai_model_id": ai_model_id,
            "start_keyframe_id": start_keyframe_id,
            "audio_id": audio_id
        }
        r = self.session.post(self._url("/generations"), json=payload, timeout=120)
        r.raise_for_status()
        return r.json()

    def get_generation_status(self, generation_id: str) -> dict:
        r = self.session.get(self._url(f"/generations/{generation_id}/status"), timeout=60)
        r.raise_for_status()
        return r.json()

    def wait_for_video_url(self, generation_id: str, timeout_sec: int = 900) -> str:
        start = time.time()
        while True:
            st = self.get_generation_status(generation_id)
            status = (st.get("status") or "").lower()

            if status in ("succeeded", "success", "completed"):
                url = (
                    st.get("asset", {}).get("url")
                    or st.get("output", {}).get("url")
                    or st.get("url")
                )
                if not url:
                    raise RuntimeError(f"Generation succeeded but no URL found. Status payload: {st}")
                return url

            if status in ("failed", "error"):
                raise RuntimeError(f"Hedra generation failed. Status payload: {st}")

            if time.time() - start > timeout_sec:
                raise TimeoutError(f"Timed out waiting for Hedra generation {generation_id}. Last status: {st}")

            time.sleep(5)

    def download_file(self, url: str, out_path: str) -> None:
        r = requests.get(url, stream=True, timeout=600)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
