from typing import Dict, Any

from flask import make_response, request
from labml_db import Model, Index
from labml_db.serializer.pickle import PickleSerializer
from labml_db.serializer.yaml import YamlSerializer

from app.logging import logger
from app.enums import INDICATORS
from ..analysis import Analysis
from ..series import SeriesModel, Series
from ..series_collection import SeriesCollection
from ..preferences import Preferences
from app.utils import format_rv
from app.utils import mix_panel


@Analysis.db_model(PickleSerializer, 'metrics')
class MetricsModel(Model['MetricsModel'], SeriesCollection):
    pass


@Analysis.db_model(PickleSerializer, 'metrics_preferences')
class MetricsPreferencesModel(Model['MetricsPreferencesModel'], Preferences):
    pass


@Analysis.db_index(YamlSerializer, 'metrics_preferences_index.yaml')
class MetricsPreferencesIndex(Index['MetricsPreferences']):
    pass


@Analysis.db_index(YamlSerializer, 'metrics_index.yaml')
class MetricsIndex(Index['Metrics']):
    pass


class MetricsAnalysis(Analysis):
    metrics: MetricsModel

    def __init__(self, data):
        self.metrics = data

    def track(self, data: Dict[str, SeriesModel]):
        res = {}
        for ind, s in data.items():
            ind_type = ind.split('.')[0]
            if ind_type not in INDICATORS:
                res[ind] = s

        self.metrics.track(res)

    def get_tracking(self):
        res = []
        for ind, track in self.metrics.tracking.items():
            name = ind.split('.')
            series: Dict[str, Any] = Series().load(track).detail
            series['name'] = '.'.join(name)

            res.append(series)

        res.sort(key=lambda s: s['name'])

        return res

    @staticmethod
    def get_or_create(run_uuid: str):
        metrics_key = MetricsIndex.get(run_uuid)

        if not metrics_key:
            m = MetricsModel()
            m.save()
            MetricsIndex.set(run_uuid, m.key)

            mp = MetricsPreferencesModel()
            mp.save()
            MetricsPreferencesIndex.set(run_uuid, mp.key)

            return MetricsAnalysis(m)

        return MetricsAnalysis(metrics_key.load())


@mix_panel.MixPanelEvent.time_this(None)
@Analysis.route('GET', 'metrics/<run_uuid>')
def get_metrics_tracking(run_uuid: str) -> Any:
    track_data = []
    status_code = 400

    ans = MetricsAnalysis.get_or_create(run_uuid)
    if ans:
        track_data = ans.get_tracking()
        status_code = 200

    response = make_response(format_rv({'series': track_data, 'insights': []}))
    response.status_code = status_code

    return response


@Analysis.route('GET', 'metrics/preferences/<run_uuid>')
def get_metrics_preferences(run_uuid: str) -> Any:
    preferences_data = {}

    preferences_key = MetricsPreferencesIndex.get(run_uuid)
    if not preferences_key:
        return format_rv(preferences_data)

    mp: MetricsPreferencesModel = preferences_key.load()
    preferences_data = mp.get_data()

    response = make_response(format_rv(preferences_data))

    return response


@Analysis.route('POST', 'metrics/preferences/<run_uuid>')
def set_metrics_preferences(run_uuid: str) -> Any:
    preferences_key = MetricsPreferencesIndex.get(run_uuid)

    if not preferences_key:
        return format_rv({})

    mp = preferences_key.load()
    mp.update_preferences(request.json)

    logger.debug(f'update metrics references: {mp.key}')

    return format_rv({'errors': mp.errors})
