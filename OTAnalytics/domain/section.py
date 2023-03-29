from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Optional

from OTAnalytics.domain.common import DataclassValidation
from OTAnalytics.domain.geometry import Coordinate

SECTIONS: str = "sections"
ID: str = "id"
TYPE: str = "type"
LINE: str = "line"
START: str = "start"
END: str = "end"
AREA: str = "area"
COORDINATES: str = "coordinates"


@dataclass(frozen=True)
class SectionId:
    id: str


class SectionListObserver(ABC):
    @abstractmethod
    def notify_sections(self, sections: list[SectionId]) -> None:
        pass


class SectionObserver(ABC):
    @abstractmethod
    def notify_section(self, section_id: Optional[SectionId]) -> None:
        pass


class SectionSubject:
    def __init__(self) -> None:
        self.observers: set[SectionObserver] = set()

    def register(self, observer: SectionObserver) -> None:
        self.observers.add(observer)

    def notify(self, section_id: Optional[SectionId]) -> None:
        [observer.notify_section(section_id) for observer in self.observers]


class SectionListSubject:
    def __init__(self) -> None:
        self.observers: set[SectionListObserver] = set()

    def register(self, observer: SectionListObserver) -> None:
        self.observers.add(observer)

    def notify(self, sections: list[SectionId]) -> None:
        [observer.notify_sections(sections) for observer in self.observers]


@dataclass(frozen=True)
class Section(DataclassValidation):
    """
    A section defines a geometry a coordinate space and is used by traffic detectors to
    create vehicle events.

    Args:
        id (str): the section id.
    """

    id: str

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Convert section into dict to interact with other parts of the system,
        e.g. serialization.

        Returns:
            dict: serialized section
        """
        pass


@dataclass(frozen=True)
class LineSection(Section):
    """
    A section that is defined by a line.

    Raises:
        ValueError: if start and end point coordinates are the same and therefore
        define a point.

    Args:
        start (Coordinate): the start coordinate.
        end (Coordinate): the end coordinate.
    """

    start: Coordinate
    end: Coordinate

    def _validate(self) -> None:
        if self.start == self.end:
            raise ValueError(
                (
                    "Start and end point of coordinate must be different to be a line, "
                    "but are same"
                )
            )

    def to_dict(self) -> dict:
        """
        Convert section into dict to interact with other parts of the system,
        e.g. serialization.
        """
        return {
            ID: self.id,
            TYPE: LINE,
            START: self.start.to_dict(),
            END: self.end.to_dict(),
        }


@dataclass(frozen=True)
class Area(Section):
    """
    A section that is defined by a polygon.

    An area is defined by `[x1, x2, x3 ..., x_n]` a list of coordinates
    where n is a natural number and `x1 = x_n`.

    Raises:
        ValueError: if coordinates do not define a closed area.
        ValueError: if the number of coordinates is less than four thus defining an
            invalid area.

    Args:
        coordinates (list[Coordinate]): area defined by list of coordinates.
    """

    coordinates: list[Coordinate]

    def _validate(self) -> None:
        if len(self.coordinates) < 4:
            raise ValueError(
                (
                    "Number of coordinates to define a valid area must be "
                    f"greater equal four, but is {len(self.coordinates)}"
                )
            )

        if self.coordinates[0] != self.coordinates[-1]:
            raise ValueError("Coordinates do not define a closed area")

    def to_dict(self) -> dict:
        """
        Convert section into dict to interact with other parts of the system,
        e.g. serialization.
        """
        return {
            TYPE: AREA,
            ID: self.id,
            COORDINATES: [coordinate.to_dict() for coordinate in self.coordinates],
        }


class SectionRepository:
    """Repository used to store sections."""

    def __init__(self) -> None:
        self._sections: dict[str, Section] = {}

    def add(self, section: Section) -> None:
        """Add a section to the repository.

        Args:
            section (Section): the section to add.
        """
        self._sections[section.id] = section

    def add_all(self, sections: Iterable[Section]) -> None:
        """Add several sections at once to the repository.

        Args:
            sections (Iterable[Section]): the sections to add.
        """
        for section in sections:
            self.add(section)

    def get_all(self) -> Iterable[Section]:
        """Get all sections from the repository.

        Returns:
            Iterable[Section]: the sections.
        """
        return self._sections.values()

    def remove(self, section: Section) -> None:
        """Remove section from the repository.

        Args:
            section (Section): the section to be removed.
        """
        del self._sections[section.id]
