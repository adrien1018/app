from typing import Dict, Any

from flask import make_response, request
from labml_db import Model, Index
from labml_db.serializer.pickle import PickleSerializer

from app.utils import format_rv
from app.logging import logger
from app.enums import COMPUTEREnums
from ..analysis import Analysis
from ..series import SeriesModel, Series
from ..series_collection import SeriesCollection
from ..preferences import Preferences


@Analysis.db_model(PickleSerializer, 'CPU')
class CPUModel(Model['CPUModel'], SeriesCollection):
    pass


@Analysis.db_index(PickleSerializer, 'cpu_index')
class CPUIndex(Index['CPU']):
    pass


@Analysis.db_model(PickleSerializer, 'cpu_preferences')
class CPUPreferencesModel(Model['CPUPreferencesModel'], Preferences):
    pass


@Analysis.db_index(PickleSerializer, 'cpu_preferences_index')
class CPUPreferencesIndex(Index['CPUPreferences']):
    pass


class CPUAnalysis(Analysis):
    cpu: CPUModel

    def __init__(self, data):
        self.cpu = data

    def track(self, data: Dict[str, SeriesModel]):
        res: Dict[str, SeriesModel] = {}
        for ind, s in data.items():
            ind_type = ind.split('.')[0]
            if ind_type == COMPUTEREnums.CPU:
                res[ind] = s

        self.cpu.track(res)

    def get_tracking(self):
        res = []
        summary = []
        for ind, track in self.cpu.tracking.items():
            name = ind.split('.')

            if any(x in ['freq', 'system', 'idle', 'user'] for x in name):
                continue

            series: Dict[str, Any] = Series().load(track).detail
            series['name'] = '.'.join(name)

            res.append(series)

        if res:
            mean_value = [sum(x) / len(x) for x in zip(*[s['value'] for s in res])]
            mean_smoothed = [sum(x) / len(x) for x in zip(*[s['smoothed'] for s in res])]
            step = res[0]['step']
            summary = [{'step': step, 'value': mean_value, 'smoothed': mean_smoothed, 'name': 'cpu.perc.total'}]

        res.sort(key=lambda s: s['name'])

        return res, summary

    @staticmethod
    def get_or_create(session_uuid: str):
        cpu_key = CPUIndex.get(session_uuid)

        if not cpu_key:
            c = CPUModel()
            c.save()
            CPUIndex.set(session_uuid, c.key)

            cp = CPUPreferencesModel()
            cp.save()
            CPUPreferencesIndex.set(session_uuid, cp.key)

            return CPUAnalysis(c)

        return CPUAnalysis(cpu_key.load())


@Analysis.route('GET', 'cpu/<session_uuid>')
def get_cpu_tracking(session_uuid: str) -> Any:
    track_data = []
    summary_data = []
    status_code = 400

    ans = CPUAnalysis.get_or_create(session_uuid)
    if ans:
        track_data, summary_data = ans.get_tracking()
        status_code = 200

    response = make_response(format_rv({'series': track_data, 'insights': [], 'summary': summary_data}))
    response.status_code = status_code

    return response


@Analysis.route('GET', 'cpu/preferences/<session_uuid>')
def get_cpu_preferences(session_uuid: str) -> Any:
    preferences_data = {}

    preferences_key = CPUPreferencesIndex.get(session_uuid)
    if not preferences_key:
        return format_rv(preferences_data)

    cp: CPUPreferencesModel = preferences_key.load()
    preferences_data = cp.get_data()

    response = make_response(format_rv(preferences_data))

    return response


@Analysis.route('POST', 'cpu/preferences/<session_uuid>')
def set_cpu_preferences(session_uuid: str) -> Any:
    preferences_key = CPUPreferencesIndex.get(session_uuid)

    if not preferences_key:
        return format_rv({})

    cp = preferences_key.load()
    cp.update_preferences(request.json)

    logger.debug(f'update cpu preferences: {cp.key}')

    return format_rv({'errors': cp.errors})
