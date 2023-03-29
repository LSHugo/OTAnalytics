import customtkinter
from customtkinter import CTk

from OTAnalytics.application.application import OTAnalyticsApplication
from OTAnalytics.application.datastore import Datastore
from OTAnalytics.application.state import TrackState
from OTAnalytics.domain.track import CalculateTrackClassificationByMaxConfidence
from OTAnalytics.plugin_parser.otvision_parser import (
    OtEventListParser,
    OtsectionParser,
    OttrkParser,
    OttrkVideoParser,
)
from OTAnalytics.plugin_ui.constants import PADX, STICKY
from OTAnalytics.plugin_ui.frame_canvas import FrameCanvas
from OTAnalytics.plugin_ui.frame_sections import FrameSections
from OTAnalytics.plugin_ui.frame_tracks import FrameTracks
from OTAnalytics.plugin_video_processing.video_reader import MoviepyVideoReader


class OTAnalyticsCli:
    def __init__(self, application: OTAnalyticsApplication) -> None:
        self._application = application

    def start(self) -> None:
        # TODO parse config and add track and section files
        pass


class OTAnalyticsGui:
    def __init__(self, application: OTAnalyticsApplication, app: CTk = CTk()) -> None:
        self._application = application
        self._app: CTk = app

    def start(self) -> None:
        self._show_gui()

    def _show_gui(self) -> None:
        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("green")

        self._app.title("OTAnalytics")

        self._get_widgets()
        self._place_widgets()
        self._wire_widgets()
        self._app.mainloop()

    def _get_widgets(self) -> None:
        self.frame_canvas = FrameCanvas(master=self._app, application=self._application)
        self.frame_tracks = FrameTracks(master=self._app, application=self._application)
        self.frame_sections = FrameSections(master=self._app)

    def _place_widgets(self) -> None:
        PADY = 10
        self.frame_canvas.grid(
            row=0, column=0, rowspan=2, padx=PADX, pady=PADY, sticky=STICKY
        )
        self.frame_tracks.grid(row=0, column=1, padx=PADX, pady=PADY, sticky=STICKY)
        self.frame_sections.grid(row=1, column=1, padx=PADX, pady=PADY, sticky=STICKY)

    def _wire_widgets(self) -> None:
        self._application.track_state.register(self.frame_canvas)


class ApplicationStarter:
    def start_gui(self) -> None:
        datastore = OTAnalyticsApplication(
            self._create_datastore(), self._create_track_state()
        )
        OTAnalyticsGui(datastore).start()

    def start_cli(self) -> None:
        datastore = OTAnalyticsApplication(
            self._create_datastore(), self._create_track_state()
        )
        OTAnalyticsCli(datastore).start()

    def _create_datastore(self) -> Datastore:
        """
        Build all required objects and inject them where necessary
        """
        track_parser = OttrkParser(CalculateTrackClassificationByMaxConfidence())
        section_parser = OtsectionParser()
        event_list_parser = OtEventListParser()
        video_parser = OttrkVideoParser(MoviepyVideoReader())
        return Datastore(track_parser, section_parser, event_list_parser, video_parser)

    def _create_track_state(self) -> TrackState:
        return TrackState()
