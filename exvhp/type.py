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

from __future__ import annotations
from typing import Literal, NotRequired, Required, TypedDict


class GfyCatItem(TypedDict):
    gfyId: str
    gfyName: str
    gfyNumber: str
    webmUrl: str
    gifUrl: str
    mobileUrl: str
    mobilePosterUrl: str
    miniUrl: str
    miniPosterUrl: str
    posterUrl: str
    thumb100PosterUrl: str
    max5mbGif: str
    max2mbGif: str
    max1mbGif: str
    gif100px: str
    width: int
    height: int
    avgColor: str
    frameRate: int
    numFrames: int
    mp4Size: int
    webmSize: int
    gifSize: int
    source: int
    createDate: int
    nsfw: str
    mp4Url: str
    likes: str
    published: int
    dislikes: str
    extraLemmas: str
    md5: str
    views: int
    tags: list[str]
    userName: str
    userName: str
    userName: str
    userName: str
    languageCategories: list[str] | None
    subreddit: str
    redditId: str
    redditIdText: str
    domainWhitelist: list[str]


class GfyCatCreatePost(TypedDict):
    fetchUrl: NotRequired[str]
    title: NotRequired[str]
    description: NotRequired[str]
    tags: NotRequired[list[str]]
    noMd5: NotRequired[bool]
    private: NotRequired[bool]
    nsfw: NotRequired[int]
    fetchSeconds: NotRequired[int]
    fetchMinutes: NotRequired[int]
    fetchHours: NotRequired[int]
    captions: NotRequired[list[GfyCatCreatePostCaption]]
    cut: NotRequired[GfyCatCreatePostCut]
    crop: NotRequired[list[GfyCatCreatePostCrop]]


class GfyCatCreatePostCaption(TypedDict):
    text: str
    startSeconds: NotRequired[int]
    duration: NotRequired[str]
    fontHeight: NotRequired[int]
    x: NotRequired[int]
    y: NotRequired[int]
    fontHeightRelative: NotRequired[int]
    xRelative: NotRequired[int]
    yRelative: NotRequired[int]


class GfyCatCreatePostCrop(TypedDict):
    x: int
    y: int
    w: int
    h: int


class GfyCatCreatePostCut(TypedDict):
    duration: int
    start: int


class GfyCatNewPost(TypedDict):
    uploadType: NotRequired[str]
    secret: NotRequired[str]
    gfyname: str


class GfyCatPostInfo(TypedDict):
    gfyItem: GfyCatItem


class GfyCatUploadError(TypedDict):
    code: str
    description: str


class GfyCatUploadStatus(TypedDict, total=False):
    task: Required[Literal["complete", "encoding", "error", "NotFoundo"]]
    time: int
    gfyname: str
    errorMessage: GfyCatUploadError


class GfyCatWebToken(TypedDict):
    access_token: str
    expires_in: int
    token_type: Literal["bearer"]


class ImgurMediaMetaData(TypedDict):
    title: str | None
    description: str | None
    is_animated: bool
    is_looping: bool
    duration: int
    has_sound: bool


class ImgurAlbumMedia(TypedDict):
    id: str
    account_id: int
    mime_type: str
    type: str
    name: str
    basename: str
    url: str
    ext: str
    width: int
    height: int
    size: int
    metadata: ImgurMediaMetaData
    created_at: str
    updated_at: str | None


class ImgurMedia(TypedDict):
    id: str
    account_id: int
    title: str | None
    description: str | None
    view_count: int
    upvote_count: int
    downvote_count: int
    point_count: int
    image_count: int
    comment_count: int
    favorite_count: int
    virality: int
    score: int
    in_most_viral: bool
    is_album: bool
    is_mature: bool
    cover_id: str
    created_at: str
    updated_at: str | None
    url: str
    privacy: Literal["private", "public"]
    vote: None
    favorite: bool
    is_ad: bool
    ad_type: int
    ad_url: str
    include_album_ads: bool
    shared_with_community: bool
    is_pending: bool
    platform: str
    media: list[ImgurAlbumMedia]
    display: list[str]


class ImgurResponse(TypedDict):
    status: int
    success: bool


class ImgurAddMediaToAlbumResponse(ImgurResponse):
    data: bool


class ImgurUpdateMediaResponse(ImgurResponse):
    data: bool


class ImgurCheckCaptchaData(TypedDict):
    OverLimit: int
    UploadCount: int
    message: str


class ImgurCheckCaptchaResponse(ImgurResponse):
    data: ImgurCheckCaptchaData


class ImgurGenerateAlbumData(TypedDict):
    id: str
    deletehash: str


class ImgurGenerateAlbumResponse(ImgurResponse):
    data: ImgurGenerateAlbumData


class ImgurUploadPollMediaData(TypedDict):
    height: str
    width: str
    deletehash: str
    size: str
    ext: str


class ImgurUploadPollData(TypedDict):
    done: dict[str, str]
    images: dict[str, ImgurUploadPollMediaData]


class ImgurUploadPollResponse(ImgurResponse):
    data: ImgurUploadPollData


class ImgurUploadTicketData(TypedDict):
    errorCode: None
    ticket: str


class ImgurUploadTicketResponse(ImgurResponse):
    data: ImgurUploadTicketData


class ImgurUploadedImageData(TypedDict):
    id: str
    title: str | None
    description: str | None
    datetime: int
    type: str
    animated: bool
    width: int
    height: int
    size: int
    views: int
    bandwidth: int
    vote: None
    favorite: bool
    nsfw: None
    section: None
    account_url: None
    account_id: int
    is_ad: bool
    in_most_viral: bool
    has_sound: bool
    tags: list[str]
    ad_type: int
    ad_url: str
    edited: str
    in_gallery: bool
    deletehash: str
    name: str
    link: str


class ImgurUploadedImageResponse(ImgurResponse):
    data: ImgurUploadedImageData


class StreamableUploadShortCodeTranscoderOptions(TypedDict, total=False):
    url: str
    token: str
    shortcode: str
    size: int


class StreamableUploadShortCodeOptions(TypedDict, total=False):
    preset: str
    screenshot: bool
    shortcode: bool


class StreamableUploadCredentials(TypedDict, total=False):
    accessKeyId: str
    secretAccessKey: str
    sessionToken: str


class StreamableVideoData(TypedDict, total=False):
    status: Required[Literal[0, 1]]
    error: str | None
    source_url: str | None
    shortcode: str
    url: str


class StreamableUploadData(TypedDict, total=False):
    shortcode: str
    timestamp: int
    bucket: str
    options: StreamableUploadShortCodeOptions
    key: str
    credentials: StreamableUploadCredentials
    url: str
    fields: dict[str, str]
    time: int
    transcoder_options: StreamableUploadShortCodeTranscoderOptions
    video: StreamableVideoData


class StreamableVideoExtractorData(TypedDict, total=False):
    error: str | None
    url: str
    video_url: str | None
    audio_url: str | None
    playback_url: str
    mime: str
    headers: dict[str, str]
    id: str
    duration: int | None
    extractor: Literal["streamable", "generic"]
    height: int | None
    width: int | None
    source_url: str
    poster_url: str | None


class StreamjaUploadUrlData(TypedDict, total=False):
    status: Required[Literal[0, 1]]
    error: str
    uploadUrl: str
    shortId: str


class StreamjaUploadData(TypedDict, total=False):
    status: Required[Literal[0, 1]]
    error: str
    shortId: str
    url: str
    image: str


class StreamffVideoData(TypedDict):
    views: int
    uploaded: bool
    publicURl: str
    date: str
    name: str
    videoLink: str
