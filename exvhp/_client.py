# eXVHP - Python Interface for Video Hosting Platforms
# Copyright (C) 2021 - eXhumer

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from datetime import datetime, timezone
from hashlib import sha256
from hmac import new as hmac_new
from io import BytesIO, IOBase, SEEK_END, SEEK_SET
from mimetypes import guess_type
from pathlib import Path
from pkg_resources import require
from typing import Dict, List, Literal, Tuple, Union
from urllib.parse import urlencode, urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import Session
from requests.structures import CaseInsensitiveDict
from requests.utils import default_user_agent as requests_user_agent
from requests_toolbelt import MultipartEncoder

from ._model import (
    FodderVideo,
    ImgurAlbumData,
    ImgurCheckCaptchaData,
    ImgurImageData,
    ImgurVideoData,
    ImgurVideoTicketData,
    JustStreamLiveVideo,
    StreamableVideo,
    StreamffVideo,
    StreamjaVideo,
)

__version__ = require(__package__)[0].version


class _ImgurClient:
    api_url = "https://api.imgur.com"
    base_url = "https://imgur.com"
    client_id = "546c25a59c58ad7"

    def __init__(self, session: Session) -> None:
        self.__session = session

    def add_media_to_album(
        self,
        album: ImgurAlbumData,
        *media_datas: ImgurImageData | ImgurVideoData,
    ):
        res = self.__session.post(
            f"{_ImgurClient.api_url}/3/album/{album.deletehash}/add",
            json={
                "deletehashes": [
                    media_data.deletehash
                    for media_data
                    in media_datas
                ],
            },
            params={"client_id": _ImgurClient.client_id},
        )
        res.raise_for_status()

        return res.json()["data"] is True

    def check_captcha(
        self,
        total_upload: int,
        g_recaptcha_response: str | None,
    ):
        res = self.__session.post(
            f"{_ImgurClient.api_url}/3/upload/checkcaptcha",
            json={
                "g-recaptcha-response": g_recaptcha_response,
                "total_upload": total_upload,
            },
            params={"client_id": _ImgurClient.client_id},
        )
        res.raise_for_status()

        return ImgurCheckCaptchaData(**res.json()["data"])

    def generate_album(self):
        res = self.__session.post(
            f"{_ImgurClient.api_url}/3/album",
            params={"client_id": _ImgurClient.client_id},
            json={},
        )
        res.raise_for_status()

        return ImgurAlbumData(**res.json()["data"])

    def get_album_medias(self, album_id: str):
        res = self.__session.get(
            f"{_ImgurClient.api_url}/post/v1/albums/{album_id}",
            params={"client_id": _ImgurClient.client_id},
        )
        res.raise_for_status()

        out: List[Tuple[str, str]] = []

        for media_data in res.json()["media"]:
            out.append((
                media_data["id"],
                media_data["url"],
            ))

        return out

    def get_media(self, media_id: str):
        res = self.__session.get(
            f"{_ImgurClient.api_url}/post/v1/media/{media_id}",
            params={"client_id": _ImgurClient.client_id},
        )
        res.raise_for_status()

        media_url: str = res.json()["url"]

        return media_id, media_url

    def get_media_content(self, media_id: str):
        media_url = self.get_media(media_id)[1]
        res = self.__session.get(media_url)
        res.raise_for_status()
        return BytesIO(res.content)

    def poll_video_tickets(self, *tickets: ImgurVideoTicketData):
        res = self.__session.get(
            f"{_ImgurClient.base_url}/upload/poll",
            params={
                "client_id": _ImgurClient.client_id,
                "tickets[]": [ticket.ticket for ticket in tickets],
            },
        )
        res.raise_for_status()

        poll_data = res.json()["data"]

        result: Dict[str, ImgurVideoData] = {}

        for ticket in tickets:
            if ticket.ticket in poll_data["done"]:
                video_id: str = poll_data["done"][ticket.ticket]
                video_deletehash: str = poll_data["images"][video_id]["deletehash"]

                result.update({
                    ticket.ticket: ImgurVideoData(
                        id=video_id,
                        deletehash=video_deletehash,
                    ),
                })

        return result

    def update_album(
        self,
        album: ImgurAlbumData,
        title: str | None = None,
        description: str | None = None,
        cover: ImgurImageData | ImgurVideoData | None = None,
        *medias: ImgurImageData | ImgurVideoData,
    ):
        album_data = {}

        if cover:
            album_data.update(cover=cover.id)

        if title:
            album_data.update(title=title)

        if description:
            album_data.update(description=description)

        if len(medias) > 0:
            album_data.update(
                deletehashes=[media.deletehash for media in medias],
            )

        res = self.__session.put(
            f"{_ImgurClient.api_url}/3/album/{album.deletehash}",
            json=album_data,
            params={"client_id": _ImgurClient.client_id},
        )
        res.raise_for_status()

        return res.json()["data"] is True

    def update_media(
        self,
        media: ImgurImageData | ImgurVideoData,
        title: str | None = None,
        description: str | None = None,
    ):
        media_data = {}

        if title:
            media_data.update(title=title)

        if description:
            media_data.update(description=description)

        res = self.__session.put(
            f"{_ImgurClient.api_url}/3/image/{media.deletehash}",
            json=media_data,
            params={"client_id": _ImgurClient.client_id},
        )
        res.raise_for_status()

        return res.json()["data"] is True

    def upload_media(
        self,
        media_io: IOBase,
        media_filename: str,
        media_mimetype: str | None = None,
    ):
        if not media_mimetype:
            media_mimetype = guess_type(media_filename, strict=False)[0]

        if not media_mimetype:
            assert False, "Unable to guess media MIME type!"

        assert media_mimetype.startswith(("image/", "video/"))

        media_name = (
            "image"
            if media_mimetype.startswith("image/")
            else "video"
        )

        media_data = MultipartEncoder({
            media_name: (
                media_filename,
                media_io,
                media_mimetype,
            ),
        })

        res = self.__session.post(
            f"{_ImgurClient.api_url}/3/image",
            data=media_data,
            headers={"Content-Type": media_data.content_type},
            params={"client_id": _ImgurClient.client_id},
        )
        res.raise_for_status()

        if media_name == "image":
            return ImgurImageData(**res.json()["data"])

        return ImgurVideoTicketData(**res.json()["data"])


class _JustStreamLiveClient:
    api_url = "https://api.juststream.live"
    base_url = "https://juststream.live"

    def __init__(self, session: Session) -> None:
        self.__session = session

    def is_video_available(self, video_id: str):
        return self.__session.get(
            f"{_JustStreamLiveClient.api_url}/videos/{video_id}"
        ).ok

    def is_video_processing(self, video_id: str):
        res = self.__session.get(f"{_StreamableClient.base_url}/{video_id}")
        res.raise_for_status()

        status = res.json()["status"]
        assert isinstance(status, str)

        return status != "COMPLETE"

    def upload_video(self, video_io: IOBase, filename: str):
        multipart_data = MultipartEncoder({
            "file": (
                filename,
                video_io,
                guess_type(filename, strict=False)[0],
            ),
        })

        res = self.__session.post(
            f"{_JustStreamLiveClient.api_url}/videos/upload",
            data=multipart_data,
            headers={"Content-Type": multipart_data.content_type},
        )
        res.raise_for_status()

        return JustStreamLiveVideo(id=res.json()["id"])


class _StreamableClient:
    api_url = "https://ajax.streamable.com"
    aws_bucket_url = "https://streamables-upload.s3.amazonaws.com"
    base_url = "https://streamable.com"
    frontend_react_version = "5a6120a04b6db864113d706cc6a6131cb8ca3587"

    @staticmethod
    def __hmac_sha256_sign(key: bytes, msg: str):
        return hmac_new(key, msg.encode("utf8"), digestmod=sha256).digest()

    @staticmethod
    def __aws_api_signing_key(
        key_secret: str,
        datestamp: str,
        region: str,
        service: str,
    ):
        key_date = _StreamableClient.__hmac_sha256_sign(
            f"AWS4{key_secret}".encode("utf8"),
            datestamp,
        )
        key_region = _StreamableClient.__hmac_sha256_sign(key_date, region)
        key_service = _StreamableClient.__hmac_sha256_sign(key_region, service)
        key_signing = _StreamableClient.__hmac_sha256_sign(
            key_service, "aws4_request",
        )
        return key_signing

    @staticmethod
    def __aws_authorization(
        method: str,
        headers: CaseInsensitiveDict,
        req_time: datetime,
        access_key_id: str,
        secret_access_key: str,
        uri: str,
        query: Dict[str, str],
        region: str,
        service: str = "s3",
    ):
        method = method.upper()
        assert method in (
            "CONNECT",
            "DELETE",
            "GET",
            "HEAD",
            "OPTIONS",
            "PATCH",
            "POST",
            "PUT",
            "TRACE",
        ), "Invalid HTTP method specified!"

        headers_dict = CaseInsensitiveDict()
        query_dict = {}

        for hk, hv in dict(sorted(headers.items())).items():
            headers_dict[hk.lower()] = hv.strip()

        assert "x-amz-content-sha256" in headers_dict, \
            "Must specify Content SHA256 for AWS request"

        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = "/".join([
            req_time.strftime("%Y%m%d"),
            region,
            service,
            "aws4_request",
        ])
        signed_headers = ";".join(headers_dict.keys())

        for qk, qv in dict(sorted(query.items())).items():
            query_dict[urlencode(qk)] = urlencode(qv)

        signature = hmac_new(
            _StreamableClient.__aws_api_signing_key(
                secret_access_key,
                req_time.strftime("%Y%m%d"),
                region,
                service,
            ),
            "\n".join((
                algorithm,
                req_time.strftime("%Y%m%dT%H%M%SZ"),
                credential_scope,
                sha256(
                    "\n".join((
                        method,
                        uri,
                        "&".join([f"{qk}:{qv}"
                                  for qk, qv
                                  in query_dict.items()]),
                        "".join([f"{hk}:{hv}\n"
                                for hk, hv
                                in headers_dict.items()]),
                        signed_headers,
                        headers_dict["x-amz-content-sha256"],
                    )).encode("utf8")
                ).hexdigest(),
            )).encode("utf8"),
            digestmod=sha256,
        ).hexdigest()

        return (
            f"{algorithm} Credential={access_key_id}/" +
            f"{credential_scope}, SignedHeaders={signed_headers}, Signature=" +
            signature
        )

    def __init__(self, session: Session) -> None:
        self.__session = session

    def __generate_clip_shortcode(
        self,
        video_id: str,
        video_source: str,
        title: str | None = None,
    ):
        res = self.__session.post(
            f"{_StreamableClient.api_url}/videos",
            json={
                "extract_id": video_id,
                "extractor": "streamable",
                "source": video_source,
                "status": 1,
                "title": title,
                "upload_source": "clip",
            },
        )
        res.raise_for_status()
        res_json = res.json()

        assert "error" not in res_json or res_json["error"] is None, \
            "Error occurred while trying to generate clip shortcode!\n" + \
            res_json["error"]

        shortcode = res_json["shortcode"]
        assert isinstance(shortcode, str)

        return shortcode

    def __generate_upload_shortcode(self, video_sz: int):
        res = self.__session.get(
            f"{_StreamableClient.api_url}/shortcode",
            params={
                "version": _StreamableClient.frontend_react_version,
                "size": video_sz,
            },
        )
        res.raise_for_status()
        res_json = res.json()

        return (
            res_json["shortcode"],
            res_json["credentials"]["accessKeyId"],
            res_json["credentials"]["secretAccessKey"],
            res_json["credentials"]["sessionToken"],
            res_json["transcoder_options"]["token"],
        )

    def __transcode_clipped_video(
        self,
        shortcode: str,
        video_headers: Dict[str, str],
        video_url: str,
        extractor: Literal["streamable", "generic"] = "generic",
        mute: bool = False,
        title: str | None = None,
    ):
        res = self.__session.post(
            f"{_StreamableClient.api_url}/transcode/{shortcode}",
            json={
                "extractor": extractor,
                "headers": video_headers,
                "mute": mute,
                "shortcode": shortcode,
                "thumb_offset": None,
                "title": title,
                "upload_source": "clip",
                "url": video_url,
            },
        )
        res.raise_for_status()

        res_json = res.json()
        assert "error" not in res_json or res_json["error"] is None, \
            "Error occurred while trying to transcode clip shortcode!\n" + \
            res_json["error"]

    def __transcode_uploaded_video(
        self,
        shortcode: str,
        transcoder_token: str,
        video_sz: int
    ):
        return self.__session.post(
            "/".join((
                _StreamableClient.api_url,
                "transcode/{shortcode}".format(shortcode=shortcode),
            )),
            json={
                "shortcode": shortcode,
                "size": video_sz,
                "token": transcoder_token,
                "upload_source": "web",
                "url": "/".join((
                    _StreamableClient.aws_bucket_url,
                    "upload/{shortcode}".format(shortcode=shortcode),
                )),
            },
        )

    def __update_upload_metadata(
        self,
        shortcode: str,
        filename: str,
        video_sz: int,
        title: str | None = None,
    ):
        res = self.__session.put(
            "/".join((
                _StreamableClient.api_url,
                "videos/{shortcode}".format(shortcode=shortcode),
            )),
            json={
                "original_name": filename,
                "original_size": video_sz,
                "title": title or Path(filename).stem,
                "upload_source": "web",
            },
            params={"purge": ""},
        )
        res.raise_for_status()

    def __video_extractor(self, url: str):
        res = self.__session.get(
            f"{_StreamableClient.api_url}/extract",
            params={"url": url},
        )
        res.raise_for_status()
        res_json = res.json()

        assert "error" not in res_json or res_json["error"] is None, \
            "Error occurred while trying to extract video URL!\n" + \
            res_json["error"]

        return res_json["url"], res_json["headers"]

    def clear_cookies(self):
        self.__session.cookies.clear(domain=".streamable.com")

    def get_video_content(self, video_id: str):
        video_url = self.get_video_url(video_id)
        res = self.__session.get(video_url)
        res.raise_for_status()
        return BytesIO(res.content)

    def get_video_url(self, video_id: str):
        res = self.__session.get(f"{_StreamableClient.base_url}/{video_id}")
        res.raise_for_status()

        vid_source_tag = BeautifulSoup(
            res.text,
            features="html.parser",
        ).find(
            "meta",
            attrs={"property": "og:video:secure_url"},
        )

        assert isinstance(vid_source_tag, Tag)

        video_source_url = vid_source_tag["content"]
        assert isinstance(video_source_url, str)

        return video_source_url

    def is_video_available(self, video_id: str):
        return self.__session.get(
            f"{_StreamableClient.base_url}/{video_id}"
        ).ok

    def is_video_processing(self, video_id: str):
        res = self.__session.get(f"{_StreamableClient.base_url}/{video_id}")
        res.raise_for_status()

        return BeautifulSoup(
            res.text,
            features="html.parser",
        ).find(
            "div",
            attrs={"id": "player-content"}
        ) is None

    def mirror_video(
        self,
        video: Union[
            ImgurVideoData,
            StreamableVideo,
            StreamffVideo,
            FodderVideo,
            StreamjaVideo,
        ],
        title: str | None = None,
    ):
        if isinstance(video, ImgurVideoData):
            imgur = _ImgurClient(self.__session)
            url, headers = self.__video_extractor(imgur.get_media(video.id)[1])

            mirror_shortcode = self.__generate_clip_shortcode(
                video.id,
                f"{_ImgurClient.base_url}/{video.id}",
                title=title,
            )

            self.__transcode_clipped_video(
                mirror_shortcode,
                headers,
                url,
                extractor="generic",
                title=title,
            )

            return StreamableVideo(shortcode=mirror_shortcode)

        elif isinstance(video, StreamableVideo):
            url, headers = self.__video_extractor(str(video.url))

            mirror_shortcode = self.__generate_clip_shortcode(
                video.shortcode,
                str(video.url),
                title=title,
            )

            self.__transcode_clipped_video(
                mirror_shortcode,
                headers,
                url,
                extractor="streamable",
                title=title,
            )

            return StreamableVideo(shortcode=mirror_shortcode)

        elif isinstance(video, StreamffVideo):
            video_url = _StreamffClient(self.__session).get_video_url(video.id)
            url, headers = self.__video_extractor(video_url)

            mirror_shortcode = self.__generate_clip_shortcode(
                video.id,
                str(video.url),
                title=title,
            )

            self.__transcode_clipped_video(
                mirror_shortcode,
                headers,
                url,
                extractor="generic",
                title=title,
            )

            return StreamableVideo(shortcode=mirror_shortcode)

        elif isinstance(video, StreamjaVideo):
            url, headers = self.__video_extractor(str(video.url))

            mirror_shortcode = self.__generate_clip_shortcode(
                video.short_id,
                str(video.url),
                title=title,
            )

            self.__transcode_clipped_video(
                mirror_shortcode,
                headers,
                url,
                extractor="generic",
                title=title,
            )

            return StreamableVideo(shortcode=mirror_shortcode)

        elif isinstance(video, FodderVideo):
            url, headers = self.__video_extractor(str(video.url))

            mirror_shortcode = self.__generate_clip_shortcode(
                video.link_id,
                str(video.url),
                title=title,
            )

            self.__transcode_clipped_video(
                mirror_shortcode,
                headers,
                url,
                extractor="generic",
                title=title,
            )

            return StreamableVideo(shortcode=mirror_shortcode)

        else:
            raise Exception("Unsupported video!")

    def upload_video(
        self,
        video_io: IOBase,
        filename: str,
        title: str | None = None,
        upload_region: str = "us-east-1",
    ):
        video_io.seek(0, SEEK_END)
        video_sz = video_io.tell()
        video_io.seek(0, SEEK_SET)

        (
            shortcode,
            access_key_id,
            secret_access_key,
            session_token,
            transcoder_token,
        ) = self.__generate_upload_shortcode(video_sz)

        self.__update_upload_metadata(
            shortcode,
            filename,
            video_sz,
            title=title,
        )

        hash = sha256()
        video_io.seek(0, SEEK_SET)

        while (len(chunk := video_io.read(4096)) > 0):
            if len(chunk) > 4096:
                raise IOError("Got more data than expected!")

            hash.update(chunk)

        video_io.seek(0, SEEK_SET)
        video_hash = hash.hexdigest()

        req_datetime = datetime.now(tz=timezone.utc)

        aws_headers = CaseInsensitiveDict()
        aws_headers["Host"] = urlparse(_StreamableClient.aws_bucket_url).netloc
        aws_headers["Content-Type"] = "application/octet-stream"
        aws_headers["X-AMZ-ACL"] = "public-read"
        aws_headers["X-AMZ-Content-SHA256"] = video_hash
        aws_headers["X-AMZ-Security-Token"] = session_token
        aws_headers["X-AMZ-Date"] = req_datetime.strftime("%Y%m%dT%H%M%SZ")
        aws_headers["Authorization"] = _StreamableClient.__aws_authorization(
            "PUT",
            aws_headers,
            req_datetime,
            access_key_id, secret_access_key,
            "/upload/{shortcode}".format(shortcode=shortcode),
            {},
            upload_region,
            service="s3",
        )

        res = self.__session.put(
            "/".join((
                _StreamableClient.aws_bucket_url,
                "upload/{shortcode}".format(shortcode=shortcode),
            )),
            data=video_io,
            headers=aws_headers,
        )
        res.raise_for_status()

        res = self.__transcode_uploaded_video(
            shortcode,
            transcoder_token,
            video_sz,
        )
        res.raise_for_status()

        return StreamableVideo(shortcode=shortcode)


class _StreamffClient:
    base_url = "https://streamff.com"

    def __init__(self, session: Session) -> None:
        self.__session = session

    def __generate_link(self):
        return self.__session.post(
            f"{_StreamffClient.base_url}/api/videos/generate-link"
        )

    def get_video_content(self, video_id: str):
        video_url = self.get_video_url(video_id)
        res = self.__session.get(video_url)
        res.raise_for_status()
        return BytesIO(res.content)

    def get_video_url(self, video_id: str):
        res = self.__session.get(
            f"{_StreamffClient.base_url}/api/videos/{video_id}"
        )
        res.raise_for_status()

        return f'{_StreamffClient.base_url}{res.json()["videoLink"]}'

    def upload_video(self, video_io: IOBase, filename: str):
        res = self.__generate_link()
        res.raise_for_status()
        video_id = res.text

        multipart_data = MultipartEncoder({
            "file": (
                filename,
                video_io,
                guess_type(filename)[0],
            ),
        })

        res = self.__session.post(
            f"{_StreamffClient.base_url}/api/videos/upload/{video_id}",
            data=multipart_data,
            headers={"Content-Type": multipart_data.content_type},
        )
        res.raise_for_status()

        return StreamffVideo(id=video_id)


class _FodderClient:
    base_url = "https://v.fodder.gg"

    def __init__(self, session: Session) -> None:
        self.__session = session

    def __generate_upload_id(self):
        res = self.__session.get(_FodderClient.base_url)
        res.raise_for_status()

        link_id_tag = BeautifulSoup(
            res.text,
            features="html.parser",
        ).find(
            "input",
            attrs={
                "type": "hidden",
                "name": "link_id",
                "id": "link_id",
            },
        )
        assert isinstance(link_id_tag, Tag)

        link_id = link_id_tag["value"]
        assert isinstance(link_id, str)

        return link_id

    def clear_cookies(self):
        self.__session.cookies.clear(domain="v.fodder.gg")

    def get_video_content(self, video_id: str):
        video_url = self.get_video_url(video_id)
        res = self.__session.get(video_url)
        res.raise_for_status()
        return BytesIO(res.content)

    def get_video_url(self, video_id: str):
        res = self.__session.get(f"{_FodderClient.base_url}/v/{video_id}")
        res.raise_for_status()

        vid_source_tag = BeautifulSoup(
            res.text,
            features="html.parser",
        ).find("source")

        assert isinstance(vid_source_tag, Tag)

        video_source_url = vid_source_tag["src"]
        assert isinstance(video_source_url, str)

        return video_source_url

    def is_video_available(self, video_id: str):
        res = self.__session.get(f"{_FodderClient.base_url}/v/{video_id}")
        res.raise_for_status()

        return (
            f"<center>This page has been removed. <small><br>id: {video_id}" +
            "</small></center>"
            not in res.text
        )

    def is_video_processing(self, video_id: str):
        res = self.__session.get(f"{_FodderClient.base_url}/v/{video_id}")
        res.raise_for_status()

        vid_source_tag = BeautifulSoup(
            res.text,
            features="html.parser",
        ).find("source")

        return vid_source_tag is None

    def upload_video(self, video_io: IOBase, filename: str):
        link_id = self.__generate_upload_id()

        multipart_data = MultipartEncoder({
            "upload_file": (
                filename,
                video_io,
                guess_type(filename)[0],
            ),
            "link_id": link_id,
        })

        res = self.__session.post(
            f"{_FodderClient.base_url}/upload_file.php",
            data=multipart_data,
            headers={"Content-Type": multipart_data.content_type},
        )
        res.raise_for_status()

        return FodderVideo(link_id=link_id)


class _StreamjaClient:
    base_url = "https://streamja.com"

    def __init__(self, session: Session) -> None:
        self.__session = session

    def __generate_upload_shortcode(self):
        return self.__session.post(
            f"{_StreamjaClient.base_url}/shortId.php",
            data={"new": 1},
        )

    def clear_cookies(self):
        self.__session.cookies.clear(domain="streamja.com")

    def get_video_content(self, video_id: str):
        video_url = self.get_video_url(video_id)
        res = self.__session.get(video_url)
        res.raise_for_status()
        return BytesIO(res.content)

    def get_video_url(self, video_id: str):
        res = self.__session.get(f"{_StreamjaClient.base_url}/{video_id}")
        res.raise_for_status()

        vid_source_tag = \
            BeautifulSoup(res.text, features="html.parser").find("source")
        assert isinstance(vid_source_tag, Tag)

        video_source_url = vid_source_tag["src"]
        assert isinstance(video_source_url, str)

        return video_source_url

    def is_video_available(self, video_id: str):
        return self.__session.get(f"{_StreamjaClient.base_url}/{video_id}").ok

    def is_video_processing(self, video_id: str):
        res = self.__session.get(f"{_StreamjaClient.base_url}/{video_id}")
        res.raise_for_status()

        return BeautifulSoup(
            res.text,
            features="html.parser",
        ).find(
            "div",
            attrs={"id": "video_container"}
        ) is None

    def upload_video(self, video_io: IOBase, filename: str):
        multipart_data = MultipartEncoder({
            "file": (
                filename,
                video_io,
                guess_type(filename)[0],
            ),
        })

        res = self.__generate_upload_shortcode()
        res.raise_for_status()

        short_id = res.json()["shortId"]

        if "error" in res.json():
            raise Exception("Error occurred while trying to generate " +
                            "Streamja video ID", res)

        res = self.__session.post(
            f"{_StreamjaClient.base_url}/upload.php",
            params={"shortId": short_id},
            data=multipart_data,
            headers={"Content-Type": multipart_data.content_type},
        )
        res.raise_for_status()

        if res.json()["status"] != 1:
            raise Exception("Error occurred while trying to upload video to " +
                            f"Streamja video ID {short_id}", res)

        return StreamjaVideo(short_id=short_id)


class Client:
    def __init__(
        self,
        session: Session | None = None,
        user_agent: str | None = None,
    ) -> None:
        if session is None:
            session = Session()

        if user_agent:
            assert session.headers["User-Agent"] == requests_user_agent(), \
                "Custom User-Agent specified both in session headers and " + \
                "in class constructor"

            session.headers["User-Agent"] = user_agent

        elif session.headers["User-Agent"] == requests_user_agent():
            session.headers["User-Agent"] = f"{__package__}/{__version__}"

        self.__imgur = _ImgurClient(session)
        self.__juststreamlive = _JustStreamLiveClient(session)
        self.__streamable = _StreamableClient(session)
        self.__streamff = _StreamffClient(session)
        self.__fodder = _FodderClient(session)
        self.__streamja = _StreamjaClient(session)

    @property
    def imgur(self):
        return self.__imgur

    @property
    def juststreamlive(self):
        return self.__juststreamlive

    @property
    def streamable(self):
        return self.__streamable

    @property
    def streamff(self):
        return self.__streamff

    @property
    def fodder(self):
        return self.__fodder

    @property
    def streamja(self):
        return self.__streamja
