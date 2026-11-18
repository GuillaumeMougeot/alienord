from core.infra.adapters.pipeline.pyds.events import EventAdapterDTO
from enum import Enum

class EventNames(str, Enum): 
    START_RECORDING = "start-recording"

event_names = ["start-recording"]

event_adapters = {
    EventNames.START_RECORDING: EventAdapterDTO()
}