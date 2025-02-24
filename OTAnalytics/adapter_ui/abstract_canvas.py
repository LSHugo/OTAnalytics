from abc import abstractmethod

from customtkinter import CTkCanvas

# from OTAnalytics.plugin_ui.canvas_observer import EventHandler


class AbstractCanvas(CTkCanvas):
    # TODO: Properly define abstract property here and in derived class(es)
    # @property
    # @abstractmethod
    # def event_handler(self) -> EventHandler:
    #     pass

    @abstractmethod
    def introduce_to_viewmodel(self) -> None:
        pass
