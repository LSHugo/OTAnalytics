from abc import ABC, abstractmethod
from typing import Callable, Generic, Iterable, Optional, TypeVar

from OTAnalytics.application.datastore import Datastore
from OTAnalytics.domain.section import (
    Section,
    SectionId,
    SectionListObserver,
    SectionObserver,
    SectionSubject,
)
from OTAnalytics.domain.track import (
    Track,
    TrackId,
    TrackImage,
    TrackListObserver,
    TrackObserver,
    TrackSubject,
)


class TrackState(TrackListObserver):
    """
    This state represents the currently selected track.
    """

    def __init__(self) -> None:
        self.selected_track: Optional[TrackId] = None
        self.observers: TrackSubject = TrackSubject()

    def register(self, observer: TrackObserver) -> None:
        """
        Listen to changes of the currently selected track.

        Args:
            observer (TrackObserver): listener to be notified about changes
        """
        self.observers.register(observer)

    def select(self, track_id: TrackId) -> None:
        """
        Select the given track.

        Args:
            track_id (TrackId): track to be selected
        """
        if self.selected_track != track_id:
            self.selected_track = track_id
            self._notify_observers()

    def _notify_observers(self) -> None:
        """
        Notify observers about the currently selected track.
        """
        self.observers.notify(self.selected_track)

    def notify_tracks(self, tracks: list[TrackId]) -> None:
        """
        Notify the state about changes in the track list.

        Args:
            tracks (list[TrackId]): newly added tracks

        Raises:
            IndexError: if the list of tracks is empty
        """
        if not tracks:
            raise IndexError("No tracks to select")
        self.select(tracks[0])


VALUE = TypeVar("VALUE")


class Observer(ABC, Generic[VALUE]):
    """
    Interface to listen to changes of a value.
    """

    @abstractmethod
    def notify(self, value: Optional[VALUE]) -> None:
        """
        Notifies that the value has changed.

        Args:
            value (Optional[VALUE]): changed value
        """
        pass


class Subject(Generic[VALUE]):
    """
    Helper class to handle and notify observers
    """

    def __init__(self) -> None:
        self.observers: set[Callable[[Optional[VALUE]], None]] = set()

    def register(self, observer: Callable[[Optional[VALUE]], None]) -> None:
        """
        Listen to events.

        Args:
            observer (Observer[VALUE]): listener to add
        """
        self.observers.add(observer)

    def notify(self, value: Optional[VALUE]) -> None:
        """
        Notifies observers about the changed value.

        Args:
            value (Optional[VALUD]): changed value
        """
        [observer(value) for observer in self.observers]


class BindableProperty(Generic[VALUE]):
    def __init__(self) -> None:
        self._property: Optional[VALUE] = None
        self._observers: Subject[VALUE] = Subject[VALUE]()

    def register(self, observer: Callable[[Optional[VALUE]], None]) -> None:
        self._observers.register(observer)

    def set(self, value: Optional[VALUE]) -> None:
        self._property = value
        self._observers.notify(value)

    def get(self) -> Optional[VALUE]:
        return self._property


class TrackViewState:
    """
    This state represents the information to be shown on the ui.
    """

    def __init__(self) -> None:
        self.background_image = BindableProperty[TrackImage]()
        self.show_tracks = BindableProperty[bool]()


class TrackPlotter(ABC):
    @abstractmethod
    def plot(
        self,
        tracks: Iterable[Track],
        sections: Iterable[Section],
        width: int,
        height: int,
        filter_classes: Iterable[str] = (
            "car",
            "motorcycle",
            "person",
            "truck",
            "bicycle",
            "train",
        ),
        num_min_frames: int = 30,
        start_time: str = "",
        end_time: str = "2022-09-15 07:05:00",
        start_end: bool = True,
        plot_sections: bool = True,
        alpha: float = 0.1,
    ) -> TrackImage:
        pass


class TrackImageUpdater(TrackListObserver):
    def __init__(
        self,
        datastore: Datastore,
        track_view_state: TrackViewState,
        track_plotter: TrackPlotter,
    ) -> None:
        self._datastore = datastore
        self._track_view_state = track_view_state
        self._track_plotter = track_plotter
        self._track_view_state.show_tracks.register(self.notify)

    def notify_tracks(self, tracks: list[TrackId]) -> None:
        if not tracks:
            raise IndexError("No tracks changed")
        self._update_image(tracks[0])

    def notify(self, show_tracks: Optional[bool]) -> None:
        if track := next(iter(self._datastore.get_all_tracks())):
            self._update_image(track.id)

    def _update_image(self, track_id: TrackId) -> None:
        if new_image := self._datastore.get_image_of_track(track_id):
            if self._track_view_state.show_tracks.get():
                track_image = self._track_plotter.plot(
                    self._datastore.get_all_tracks(),
                    self._datastore.get_all_sections(),
                    width=new_image.width(),
                    height=new_image.height(),
                )
                combined_image = new_image.add(track_image)
                self._track_view_state.background_image.set(combined_image)
            else:
                self._track_view_state.background_image.set(new_image)


class SectionState(SectionListObserver):
    """
    This state represents the currently selected section.
    """

    def __init__(self) -> None:
        self.selected_section: Optional[SectionId] = None
        self.observers: SectionSubject = SectionSubject()

    def register(self, observer: SectionObserver) -> None:
        """
        Listen to changes of the currently selected section.

        Args:
            observer (SectionObserver): listener to be notified about changes
        """
        self.observers.register(observer)

    def select(self, section_id: SectionId) -> None:
        """
        Select the given section.

        Args:
            section_id (SectionId): section to be selected
        """
        if self.selected_section != section_id:
            self.selected_section = section_id
            self._notify_observers()

    def _notify_observers(self) -> None:
        """
        Notify observers about the currently selected section.
        """
        self.observers.notify(self.selected_section)

    def notify_sections(self, sections: list[SectionId]) -> None:
        """
        Notify the state about changes in the section list.

        Args:
            sections (list[SectionId]): newly added sections

        Raises:
            IndexError: if the list of sections is empty
        """
        if not sections:
            raise IndexError("No section to select")
        self.select(sections[0])
