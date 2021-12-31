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

from pydantic import BaseModel, HttpUrl, validator


class JustStreamLiveVideo(BaseModel):
    id: str
    url: HttpUrl = None

    @validator("url", pre=True, always=True)
    def url_validator(cls, v, values, **kwargs):
        return f"https://juststream.live/{values['id']}"


class MixtureVideo(BaseModel):
    link_id: str
    url: HttpUrl = None

    @validator("url", pre=True, always=True)
    def url_validator(cls, v, values, **kwargs):
        return f"https://mixture.gg/v/{values['link_id']}"


class StreamableVideo(BaseModel):
    shortcode: str
    url: HttpUrl = None

    @validator("url", pre=True, always=True)
    def url_validator(cls, v, values, **kwargs):
        return f"https://streamable.com/{values['shortcode']}"


class StreamffVideo(BaseModel):
    id: str
    url: HttpUrl = None

    @validator("url", pre=True, always=True)
    def url_validator(cls, v, values, **kwargs):
        return f"https://streamff.com/v/{values['id']}"


class StreamjaVideo(BaseModel):
    short_id: str
    url: HttpUrl = None
    embed_url: HttpUrl = None

    @validator("embed_url", pre=True, always=True)
    def embed_url_validator(cls, v, values, **kwargs):
        return f"https://streamja.com/embed/{values['short_id']}"

    @validator("url", pre=True, always=True)
    def url_validator(cls, v, values, **kwargs):
        return f"https://streamja.com/{values['short_id']}"


class StreamwoVideo(BaseModel):
    link_id: str
    url: HttpUrl = None

    @validator("url", pre=True, always=True)
    def url_validator(cls, v, values, **kwargs):
        return f"https://streamwo.com/file/{values['link_id']}"
