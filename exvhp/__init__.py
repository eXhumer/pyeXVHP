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

from ._client import Client  # noqa: F401
from ._model import (  # noqa: F401
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
