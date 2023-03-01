# pyeXVHP - Python Interface for Video Hosting Platforms
# Copyright © 2023 - eXhumer

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3 of the License.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from hmac import new as hmac_new
from io import SEEK_END, SEEK_SET
from mimetypes import guess_type
from pathlib import Path
from pkg_resources import require
from typing import BinaryIO, Dict, Literal
from urllib.parse import urlencode, urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag
from httpx import Client

from .type import (
    GfyCatCreatePost,
    GfyCatNewPost,
    GfyCatPostInfo,
    GfyCatUploadStatus,
    GfyCatWebToken,
    ImgurAddMediaToAlbumResponse,
    ImgurCheckCaptchaResponse,
    ImgurGenerateAlbumResponse,
    ImgurMedia,
    ImgurUpdateMediaResponse,
    ImgurUploadedImageResponse,
    ImgurUploadPollResponse,
    ImgurUploadTicketResponse,
    StreamableUploadData,
    StreamableVideoData,
    StreamableVideoExtractorData,
    StreamjaUploadUrlData,
    StreamjaUploadData,
    StreamffVideoData,
)

try:
    import h2  # noqa: F401
    h2_available = True

except ImportError:
    h2_available = False

__version__ = require(__package__)[0].version
__user_agent__ = f"{__package__}/{__version__}"


class GfyCatClient:
    api_url = "https://api.gfycat.com"
    weblogin_url = "https://weblogin.gfycat.com"
    webtoken_access_key = "Anr96uuqt9EdamSCwK4txKPjMsf2M95Rfa5FLLhPFucu8H5HTzeutyAa"

    def __init__(self, client: Client | None = None, user_agent: str | None = None):
        client = client or Client(http2=h2_available)
        client.headers["User-Agent"] = user_agent or __user_agent__

        self.__authorization = None
        self.__expires_at = None
        self.__client = client
        self.__obtain_authorization()

    def __obtain_authorization(self):
        res = self.__client.post(f"{self.weblogin_url}/oauth/webtoken",
                                 json={"access_key": self.webtoken_access_key})

        if res.status_code >= 400:
            res.raise_for_status()

        token_data: GfyCatWebToken = res.json()
        access_token = token_data["access_token"]
        token_type = token_data["token_type"]
        expires_in = token_data["expires_in"]

        self.__expires_at = parsedate_to_datetime(res.headers["Date"]) + \
            timedelta(seconds=expires_in)
        self.__authorization = f"{token_type} {access_token}"

    def delete_post(self, gfyname: str):
        if datetime.now(tz=timezone.utc) >= self.__expires_at:
            self.__obtain_authorization()

        res = self.__client.delete(f"{self.api_url}/v1/gfycats/{gfyname}",
                                   headers={"Authorization": self.__authorization})

        if res.status_code >= 400:
            res.raise_for_status()

        return res.status_code < 400

    def get_post_info(self, gfyid: str):
        if datetime.now(tz=timezone.utc) >= self.__expires_at:
            self.__obtain_authorization()

        res = self.__client.get(f"{self.api_url}/v1/gfycats/{gfyid}",
                                headers={"Authorization": self.__authorization})

        if res.status_code >= 400:
            res.raise_for_status()

        post_info: GfyCatPostInfo = res.json()

        return post_info

    def get_upload_status(self, gfyid: str):
        if datetime.now(tz=timezone.utc) >= self.__expires_at:
            self.__obtain_authorization()

        res = self.__client.get(f"{self.api_url}/v1/gfycats/fetch/status/{gfyid}",
                                headers={"Authorization": self.__authorization})

        if res.status_code >= 400:
            res.raise_for_status()

        post_status: GfyCatUploadStatus = res.json()

        return post_status

    def new_video_post(self, post_data: GfyCatCreatePost | None = None):
        if datetime.now(tz=timezone.utc) >= self.__expires_at:
            self.__obtain_authorization()

        res = self.__client.post(f"{self.api_url}/v1/gfycats", json=post_data,
                                 headers={"Authorization": self.__authorization})

        if res.status_code >= 400:
            res.raise_for_status()

        new_post_data: GfyCatNewPost = res.json()

        return new_post_data

    def upload_video(self, gfyname: str, media_io: BinaryIO, filename: str = "video.mp4",
                     upload_type: str = "filedrop.gfycat.com"):
        res = self.__client.post(f"https://{upload_type}/", data={"key": gfyname},
                                 files={"file": (filename, media_io, guess_type(filename)[0])})

        if res.status_code >= 400:
            res.raise_for_status()

        return res.status_code < 400


class ImgurClient:
    api_url = "https://api.imgur.com"
    base_url = "https://imgur.com"
    client_id = "546c25a59c58ad7"

    def __init__(self, client: Client | None = None, user_agent: str | None = None):
        client = client or Client(http2=h2_available)
        client.headers["User-Agent"] = user_agent or __user_agent__
        self.__client = client

    def add_media_to_album(self, album_deletehash: str, *media_deletehashes: str):
        res = self.__client.post(f"{self.api_url}/3/album/{album_deletehash}/add",
                                 json={"deletehashes": [dh for dh in media_deletehashes]},
                                 params={"client_id": self.client_id})

        if res.status_code >= 400:
            res.raise_for_status()

        data: ImgurAddMediaToAlbumResponse = res.json()

        return data

    def check_captcha(self, total_upload: int, g_recaptcha_response: str | None = None):
        res = self.__client.post(f"{self.api_url}/3/upload/checkcaptcha",
                                 json={
                                     "g-recaptcha-response": g_recaptcha_response,
                                     "total_upload": total_upload,
                                 },
                                 params={"client_id": self.client_id})

        if res.status_code >= 400:
            res.raise_for_status()

        data: ImgurCheckCaptchaResponse = res.json()

        return data

    def generate_album(self):
        res = self.__client.post(f"{self.api_url}/3/album", params={"client_id": self.client_id},
                                 json={})

        if res.status_code >= 400:
            res.raise_for_status()

        data: ImgurGenerateAlbumResponse = res.json()

        return data

    def get_album_medias(self, album_id: str):
        res = self.__client.get(f"{self.api_url}/post/v1/albums/{album_id}",
                                params={"client_id": self.client_id, "include": "media"})

        if res.status_code >= 400:
            res.raise_for_status()

        data: ImgurMedia = res.json()

        return data

    def get_media(self, media_id: str):
        res = self.__client.get(f"{self.api_url}/post/v1/media/{media_id}",
                                params={"client_id": self.client_id, "include": "media"})

        if res.status_code >= 400:
            res.raise_for_status()

        data: ImgurMedia = res.json()

        return data

    def poll_video_tickets(self, *tickets: str):
        res = self.__client.get(f"{self.base_url}/upload/poll",
                                params={
                                    "client_id": self.client_id,
                                    "tickets[]": [ticket for ticket in tickets],
                                })

        if res.status_code >= 400:
            res.raise_for_status()

        poll_data: ImgurUploadPollResponse = res.json()

        return poll_data

    def update_album(self, album_deletehash: str, title: str | None = None,
                     description: str | None = None, cover_id: str | None = None,
                     *media_deletehashes: str):
        album_data = {}

        if cover_id:
            album_data.update(cover=cover_id)

        if title:
            album_data.update(title=title)

        if description:
            album_data.update(description=description)

        if len(media_deletehashes) > 0:
            album_data.update(deletehashes=[dh for dh in media_deletehashes])

        res = self.__client.put(f"{self.api_url}/3/album/{album_deletehash}", json=album_data,
                                params={"client_id": self.client_id})

        if res.status_code >= 400:
            res.raise_for_status()

        data: ImgurUpdateMediaResponse = res.json()

        return data

    def update_media(self, media_deletehash: str, title: str | None = None,
                     description: str | None = None):
        media_data = {}

        if title:
            media_data.update(title=title)

        if description:
            media_data.update(description=description)

        res = self.__client.put(f"{self.api_url}/3/image/{media_deletehash}", json=media_data,
                                params={"client_id": self.client_id})

        if res.status_code >= 400:
            res.raise_for_status()

        data: ImgurUpdateMediaResponse = res.json()

        return data

    def upload_media(self, media_io: BinaryIO, media_filename: str,
                     media_mimetype: str | None = None):
        if not media_mimetype:
            media_mimetype = guess_type(media_filename, strict=False)[0]

        if not media_mimetype:
            assert False, "Unable to guess media MIME type!"

        assert media_mimetype.startswith(("image/", "video/"))

        media_name = "image" if media_mimetype.startswith("image/") else "video"
        files = {media_name: (media_filename, media_io, media_mimetype)}

        res = self.__client.post(f"{self.api_url}/3/image", files=files,
                                 params={"client_id": self.client_id})

        if res.status_code >= 400:
            res.raise_for_status()

        data: ImgurUploadedImageResponse | ImgurUploadTicketResponse = res.json()

        return data


class StreamableClient:
    api_url = "https://ajax.streamable.com"
    base_url = "https://streamable.com"
    frontend_react_version = "5a6120a04b6db864113d706cc6a6131cb8ca3587"

    @staticmethod
    def __hmac_sha256_sign(key: bytes, msg: str):
        return hmac_new(key, msg.encode(encoding="utf8"), digestmod=sha256).digest()

    @staticmethod
    def __aws_api_signing_key(key_secret: str, datestamp: str, region: str, service: str):
        key_date = StreamableClient.__hmac_sha256_sign(
            f"AWS4{key_secret}".encode(encoding="utf8"), datestamp)
        key_region = StreamableClient.__hmac_sha256_sign(key_date, region)
        key_service = StreamableClient.__hmac_sha256_sign(key_region, service)
        key_signing = StreamableClient.__hmac_sha256_sign(key_service, "aws4_request")
        return key_signing

    @staticmethod
    def __aws_authorization(method: str, headers: dict[str, str], req_time: datetime,
                            access_key_id: str, secret_access_key: str, uri: str,
                            query: Dict[str, str], region: str, service: str):
        method = method.upper()
        assert method in ("CONNECT", "DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT",
                          "TRACE"), "Invalid HTTP method specified!"

        hd = {}
        qd = {}

        for hk, hv in dict(sorted(headers.items())).items():
            hd[hk.lower()] = hv.strip()

        assert "x-amz-content-sha256" in hd, \
            "Must specify Content SHA256 for AWS request"

        algo = "AWS4-HMAC-SHA256"
        cs = "/".join([req_time.strftime("%Y%m%d"), region, service, "aws4_request"])
        sh = ";".join(hd.keys())

        for qk, qv in dict(sorted(query.items())).items():
            qd[urlencode(qk)] = urlencode(qv)

        hs = "".join([f"{hk}:{hv}\n" for hk, hv in hd.items()])
        qs = "&".join([f"{qk}:{qv}" for qk, qv in qd.items()])
        rs = "\n".join((method, uri, qs, hs, sh, hd["x-amz-content-sha256"]))
        ss = "\n".join((algo, req_time.strftime("%Y%m%dT%H%M%SZ"), cs,
                        sha256(rs.encode(encoding="utf8")).hexdigest()))
        signature = hmac_new(
            StreamableClient.__aws_api_signing_key(secret_access_key, req_time.strftime("%Y%m%d"),
                                                   region, service),
            ss.encode(encoding="utf8"),
            digestmod=sha256,
        ).hexdigest()

        return f"{algo} Credential={access_key_id}/{cs}, SignedHeaders={sh}, Signature={signature}"

    def __init__(self, client: Client | None = None, user_agent: str | None = None):
        client = client or Client(http2=h2_available)
        client.headers["User-Agent"] = user_agent or __user_agent__
        self.__client = client

    def __generate_clip_shortcode(self, video_id: str, video_source: str,
                                  title: str | None = None):
        res = self.__client.post(f"{self.api_url}/videos",
                                 json={
                                     "extract_id": video_id,
                                     "extractor": (
                                       "streamable"
                                       if video_source.startswith("https://streamable.com")
                                       else "generic"
                                     ),
                                     "source": video_source,
                                     "status": 1,
                                     "title": title,
                                     "upload_source": "clip",
                                 })

        if res.status_code >= 400:
            res.raise_for_status()

        res_json: StreamableVideoData = res.json()

        return res_json

    def __generate_upload_shortcode(self, video_sz: int):
        res = self.__client.get(f"{self.api_url}/shortcode",
                                params={
                                    "version": self.frontend_react_version,
                                    "size": video_sz,
                                })

        if res.status_code >= 400:
            res.raise_for_status()

        res_json: StreamableUploadData = res.json()

        return res_json

    def __transcode_clipped_video(self, shortcode: str, video_headers: Dict[str, str],
                                  video_url: str,
                                  extractor: Literal["streamable", "generic"] = "generic",
                                  mute: bool = False, title: str | None = None):
        res = self.__client.post(f"{self.api_url}/transcode/{shortcode}",
                                 json={
                                     "extractor": extractor,
                                     "headers": video_headers,
                                     "mute": mute,
                                     "shortcode": shortcode,
                                     "thumb_offset": None,
                                     "title": title,
                                     "upload_source": "clip",
                                     "url": video_url,
                                 })

        if res.status_code >= 400:
            res.raise_for_status()

        res_json: StreamableVideoData = res.json()

        return res_json

    def __transcode_uploaded_video(self, shortcode: str, url: str, transcoder_token: str,
                                   video_sz: int):
        res = self.__client.post(f"{self.api_url}/transcode/{shortcode}",
                                 json={
                                     "shortcode": shortcode,
                                     "size": video_sz,
                                     "token": transcoder_token,
                                     "upload_source": "web",
                                     "url": url,
                                 })

        if res.status_code >= 400:
            res.raise_for_status()

        res_json: StreamableVideoData = res.json()

        return res_json

    def __update_upload_metadata(self, shortcode: str, filename: str, video_sz: int,
                                 title: str | None = None):
        res = self.__client.put(f"{self.api_url}/videos/{shortcode}", params={"purge": ""},
                                json={
                                    "original_name": filename,
                                    "original_size": video_sz,
                                    "title": title or Path(filename).stem,
                                    "upload_source": "web",
                                })

        if res.status_code >= 400:
            res.raise_for_status()

        res_json: StreamableVideoData = res.json()

        return res_json

    def clear_cookies(self):
        self.__client.cookies.clear(domain=".streamable.com")

    def clip_video(self, video_url: str, title: str | None = None):
        extractor_data = self.video_extractor(video_url)
        video_data = self.__generate_clip_shortcode(extractor_data["id"], video_url, title=title)
        self.__transcode_clipped_video(video_data["shortcode"], extractor_data["headers"],
                                       extractor_data["url"],
                                       extractor=extractor_data["extractor"], title=title)
        return video_data

    def get_video_url(self, video_id: str):
        res = self.__client.get(f"{StreamableClient.base_url}/{video_id}")

        if res.status_code >= 400:
            res.raise_for_status()

        vid_source_tag = BeautifulSoup(res.text, features="html.parser").find(
            "meta",
            attrs={"property": "og:video:secure_url"})

        assert isinstance(vid_source_tag, Tag)

        video_source_url = vid_source_tag["content"]
        assert isinstance(video_source_url, str)

        return video_source_url

    def is_video_available(self, video_id: str):
        return self.__client.get(f"{self.base_url}/{video_id}").ok

    def is_video_processing(self, video_id: str):
        res = self.__client.get(f"{StreamableClient.base_url}/{video_id}")

        if res.status_code >= 400:
            res.raise_for_status()

        player_tag = BeautifulSoup(res.text, features="html.parser").find(
            "div", attrs={"id": "player-content"})

        return player_tag is None

    def upload_video(self, video_io: BinaryIO, filename: str = "video.mp4",
                     title: str | None = None, upload_region: str = "us-east-1"):
        video_io.seek(0, SEEK_END)
        video_sz = video_io.tell()
        video_io.seek(0, SEEK_SET)

        upload_data = self.__generate_upload_shortcode(video_sz)
        self.__update_upload_metadata(upload_data["shortcode"], filename, video_sz, title=title)

        hash = sha256()
        video_io.seek(0, SEEK_SET)

        while (len(chunk := video_io.read(4096)) > 0):
            if len(chunk) > 4096:
                raise IOError("Got more data than expected!")

            hash.update(chunk)

        video_io.seek(0, SEEK_SET)
        video_hash = hash.hexdigest()

        req_datetime = datetime.now(tz=timezone.utc)

        aws_headers = {}
        aws_headers["Host"] = urlparse(upload_data["url"]).netloc
        aws_headers["Content-Type"] = "application/octet-stream"
        aws_headers["X-AMZ-ACL"] = "public-read"
        aws_headers["X-AMZ-Content-SHA256"] = video_hash
        aws_headers["X-AMZ-Security-Token"] = upload_data["credentials"]["sessionToken"]
        aws_headers["X-AMZ-Date"] = req_datetime.strftime("%Y%m%dT%H%M%SZ")
        aws_headers["Authorization"] = StreamableClient.__aws_authorization(
            "PUT", aws_headers, req_datetime, upload_data["credentials"]["accessKeyId"],
            upload_data["credentials"]["secretAccessKey"], "/" + upload_data["key"], {},
            upload_region, "s3")

        res = self.__client.put(upload_data["transcoder_options"]["url"], data=video_io,
                                headers=aws_headers)

        if res.status_code >= 400:
            res.raise_for_status()

        return self.__transcode_uploaded_video(upload_data["transcoder_options"]["shortcode"],
                                               upload_data["transcoder_options"]["url"],
                                               upload_data["transcoder_options"]["token"],
                                               upload_data["transcoder_options"]["size"])

    def video_extractor(self, url: str):
        res = self.__client.get(f"{self.api_url}/extract", params={"url": url})

        if res.status_code >= 400:
            res.raise_for_status()

        res_json: StreamableVideoExtractorData = res.json()

        assert "error" not in res_json or res_json["error"] is None, \
            "Error occurred while trying to extract video URL!\n" + \
            res_json["error"]

        return res_json


class StreamffClient:
    base_url = "https://streamff.com"

    def __init__(self, client: Client | None = None, user_agent: str | None = None):
        client = client or Client(http2=h2_available)
        client.headers["User-Agent"] = user_agent or __user_agent__
        self.__client = client

    def __generate_link(self):
        return self.__client.post(f"{self.base_url}/api/videos/generate-link")

    def get_video_data(self, video_id: str):
        res = self.__client.get(f"{self.base_url}/api/videos/{video_id}")

        if res.status_code >= 400:
            res.raise_for_status()

        res_json: StreamffVideoData = res.json()
        return res_json

    def upload_video(self, video_io: BinaryIO, filename: str = "video.mp4"):
        res = self.__generate_link()

        if res.status_code >= 400:
            res.raise_for_status()

        video_id = res.text

        video_mimetype = guess_type(filename, strict=False)[0]
        assert video_mimetype is not None and video_mimetype.startswith("video/")
        files = {"file": (filename, video_io, video_mimetype)}

        res = self.__client.post(f"{self.base_url}/api/videos/upload/{video_id}", files=files)

        if res.status_code >= 400:
            res.raise_for_status()

        return video_id, f"https://streamff.com/v/{video_id}"


class StreamjaClient:
    base_url = "https://streamja.com"

    def __init__(self, client: Client | None = None, user_agent: str | None = None):
        client = client or Client(http2=h2_available)
        client.headers["User-Agent"] = user_agent or __user_agent__
        self.__client = client

    def __generate_upload_shortcode(self):
        res = self.__client.post(f"{StreamjaClient.base_url}/shortId.php", data={"new": 1})

        if res.status_code >= 400:
            res.raise_for_status()

        res_json: StreamjaUploadUrlData = res.json()
        return res_json

    def clear_cookies(self):
        self.__client.cookies.clear(domain="streamja.com")

    def get_video_url(self, video_id: str):
        res = self.__client.get(f"{StreamjaClient.base_url}/{video_id}")

        if res.status_code >= 400:
            res.raise_for_status()

        vid_source_tag = BeautifulSoup(res.text, features="html.parser").find("source")
        assert isinstance(vid_source_tag, Tag)

        vid_src_url = vid_source_tag["src"]
        assert isinstance(vid_src_url, str)

        return vid_src_url

    def is_video_available(self, video_id: str):
        return self.__client.get(f"{StreamjaClient.base_url}/{video_id}").ok

    def is_video_processing(self, video_id: str):
        res = self.__client.get(f"{StreamjaClient.base_url}/{video_id}")

        if res.status_code >= 400:
            res.raise_for_status()

        video_container = BeautifulSoup(res.text, features="html.parser").find(
            "div", attrs={"id": "video_container"})
        return video_container is None

    def upload_video(self, video_io: BinaryIO, filename: str = "video.mp4"):
        video_mimetype = guess_type(filename, strict=False)[0]
        assert video_mimetype is not None and video_mimetype.startswith("video/")
        files = {"file": (filename, video_io, video_mimetype)}
        generate_shortcode_data = self.__generate_upload_shortcode()

        if generate_shortcode_data["status"] == 0 or "error" in generate_shortcode_data:
            raise Exception("Error occurred while trying to generate Streamja video ID",
                            generate_shortcode_data)

        else:
            assert "shortId" in generate_shortcode_data
            assert "uploadUrl" in generate_shortcode_data

        short_id = generate_shortcode_data["shortId"]
        res = self.__client.post(f"{StreamjaClient.base_url}/upload.php", files=files,
                                 params={"shortId": short_id})

        if res.status_code >= 400:
            res.raise_for_status()

        res_json: StreamjaUploadData = res.json()

        if res_json["status"] == 0 or "error" in res_json:
            raise Exception("Error occurred while trying to upload video to Streamja video ID " +
                            short_id, res_json)

        else:
            assert "image" in res_json
            assert "shortId" in res_json
            assert "url" in res_json

        return res_json


class VHPClient:
    __CLIENT = Client(http2=h2_available)
    __CLIENT.headers["User-Agent"] = __user_agent__

    def __init__(self, client: Client | None = None, user_agent: str | None = None):
        client = client or VHPClient.__CLIENT
        self.__gfycat = GfyCatClient(client=client, user_agent=user_agent)
        self.__imgur = ImgurClient(client=client, user_agent=user_agent)
        self.__streamable = StreamableClient(client=client, user_agent=user_agent)
        self.__streamff = StreamffClient(client=client, user_agent=user_agent)
        self.__streamja = StreamjaClient(client=client, user_agent=user_agent)

    @property
    def gfycat(self):
        return self.__gfycat

    @property
    def imgur(self):
        return self.__imgur

    @property
    def streamable(self):
        return self.__streamable

    @property
    def streamff(self):
        return self.__streamff

    @property
    def streamja(self):
        return self.__streamja
