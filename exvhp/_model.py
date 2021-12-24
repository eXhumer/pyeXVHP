from pydantic import BaseModel, HttpUrl, validator


class JustStreamLiveVideo(BaseModel):
    id: str
    url: HttpUrl = None

    @validator("url", pre=True, always=True)
    def url_validator(cls, v, values, **kwargs):
        return f"https://juststream.live/{values['id']}"


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
