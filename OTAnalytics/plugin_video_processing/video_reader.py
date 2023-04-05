from dataclasses import dataclass
from pathlib import Path

from moviepy.video.io.VideoFileClip import VideoFileClip
from numpy import ndarray
from PIL import Image

from OTAnalytics.application.datastore import VideoReader
from OTAnalytics.domain.track import TrackImage


class FrameDoesNotExistError(Exception):
    pass


@dataclass(frozen=True)
class NdArrayImage(TrackImage):
    _image: ndarray

    def as_image(self) -> Image.Image:
        return Image.fromarray(self._image)

    def width(self) -> int:
        return self._image.shape[1]

    def height(self) -> int:
        return self._image.shape[0]


class MoviepyVideoReader(VideoReader):
    def get_frame(self, video_path: Path, index: int) -> TrackImage:
        """Get image of video at `frame`.

        Args:
            video_path (Path): path to the video_path.
            index (int): the frame of the video to get.

        Raises:
            FrameDoesNotExistError: if frame does not exist.

        Returns:
            ndarray: the image as an multi-dimensional array.
        """
        clip = VideoFileClip(str(video_path.absolute()))
        found = None
        for frame_no, np_frame in enumerate(clip.iter_frames()):
            if frame_no == index:
                found = np_frame
                break
        clip.close()
        if found is None:
            raise FrameDoesNotExistError(f"frame number '{index}' does not exist")
        return NdArrayImage(found)
