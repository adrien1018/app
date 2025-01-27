from typing import Dict, Any

from flask import jsonify, make_response, request
from labml_db import Model, Index
from labml_db.serializer.pickle import PickleSerializer
from labml_db.serializer.yaml import YamlSerializer

from app.utils import format_rv
from app.logging import logger
from app.enums import COMPUTEREnums
from ..analysis import Analysis
from ..series import SeriesModel, Series
from ..series_collection import SeriesCollection
from ..preferences import Preferences


@Analysis.db_model(PickleSerializer, 'Memory')
class MemoryModel(Model['MemoryModel'], SeriesCollection):
    pass


@Analysis.db_index(YamlSerializer, 'memory_index')
class MemoryIndex(Index['Memory']):
    pass


@Analysis.db_model(PickleSerializer, 'memory_preferences')
class MemoryPreferencesModel(Model['MemoryPreferencesModel'], Preferences):
    pass


@Analysis.db_index(YamlSerializer, 'memory_preferences_index')
class MemoryPreferencesIndex(Index['MemoryPreferences']):
    pass


class MemoryAnalysis(Analysis):
    memory: MemoryModel

    def __init__(self, data):
        self.memory = data

    def track(self, data: Dict[str, SeriesModel]):
        res: Dict[str, SeriesModel] = {}
        for ind, s in data.items():
            ind_type = ind.split('.')[0]
            if ind_type == COMPUTEREnums.MEMORY:
                res[ind] = s

        self.memory.track(res)

    def get_tracking(self):
        res = []
        for ind, track in self.memory.tracking.items():
            name = ind.split('.')

            if any(x in ['total'] for x in name):
                continue

            series: Dict[str, Any] = Series().load(track).detail
            series['name'] = '.'.join(name)

            res.append(series)

        res.sort(key=lambda s: s['name'])

        return res

    @staticmethod
    def get_or_create(session_uuid: str):
        cpu_key = MemoryIndex.get(session_uuid)

        if not cpu_key:
            m = MemoryModel()
            m.save()
            MemoryIndex.set(session_uuid, m.key)

            mp = MemoryPreferencesModel()
            mp.save()
            MemoryPreferencesIndex.set(session_uuid, mp.key)

            return MemoryAnalysis(m)

        return MemoryAnalysis(cpu_key.load())


@Analysis.route('GET', 'memory/<session_uuid>')
def get_memory_tracking(session_uuid: str) -> Any:
    track_data = []
    status_code = 400

    ans = MemoryAnalysis.get_or_create(session_uuid)
    if ans:
        track_data = ans.get_tracking()
        status_code = 200

    response = make_response(format_rv({'series': track_data, 'insights': [], 'summary': track_data}))
    response.status_code = status_code

    return response


@Analysis.route('GET', 'memory/preferences/<session_uuid>')
def get_memory_preferences(session_uuid: str) -> Any:
    preferences_data = {}

    preferences_key = MemoryPreferencesIndex.get(session_uuid)
    if not preferences_key:
        return format_rv(preferences_data)

    mp: MemoryPreferencesModel = preferences_key.load()
    preferences_data = mp.get_data()

    response = make_response(format_rv(preferences_data))

    return response


@Analysis.route('POST', 'memory/preferences/<session_uuid>')
def set_memory_preferences(session_uuid: str) -> Any:
    preferences_key = MemoryPreferencesIndex.get(session_uuid)

    if not preferences_key:
        return format_rv({})

    mp = preferences_key.load()
    mp.update_preferences(request.json)

    logger.debug(f'update memory preferences: {mp.key}')

    return format_rv({'errors': mp.errors})
