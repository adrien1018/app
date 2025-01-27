import time
from typing import Dict, List, Optional, Union, NamedTuple

from labml_db import Model, Key, Index

from ..utils.mix_panel import MixPanelEvent
from . import project
from .status import create_status, Status
from .. import settings
from ..logging import logger


class CardInfo(NamedTuple):
    class_name: str
    name: str
    is_print: bool
    queue_size: int = 0


class Run(Model['Run']):
    name: str
    comment: str
    note: str
    tags: List[str]
    start_time: float
    run_ip: str
    run_uuid: str
    python_file: str
    repo_remotes: str
    commit: str
    commit_message: str
    start_step: int
    is_claimed: bool
    status: Key[Status]
    configs: Dict[str, any]
    stdout: str
    stdout_unmerged: str
    logger: str
    logger_unmerged: str
    stderr: str
    stderr_unmerged: str

    wildcard_indicators: Dict[str, Dict[str, Union[str, bool]]]
    indicators: Dict[str, Dict[str, Union[str, bool]]]
    errors: List[Dict[str, str]]

    @classmethod
    def defaults(cls):
        return dict(name='',
                    comment='',
                    note='',
                    tags=[],
                    start_time=None,
                    run_uuid='',
                    python_file='',
                    repo_remotes='',
                    commit='',
                    commit_message='',
                    start_step=None,
                    run_ip='',
                    is_claimed=True,
                    status=None,
                    configs={},
                    stdout='',
                    stdout_unmerged='',
                    logger='',
                    logger_unmerged='',
                    stderr='',
                    stderr_unmerged='',
                    wildcard_indicators={},
                    indicators={},
                    errors=[]
                    )

    @property
    def url(self) -> str:
        return f'{settings.WEB_URL}/run?uuid={self.run_uuid}'

    def update_run(self, data: Dict[str, any]) -> None:
        if not self.name:
            self.name = data.get('name', '')
        if not self.comment:
            self.comment = data.get('comment', '')
        if not self.tags:
            self.tags = data.get('tags', '')
        if not self.python_file:
            self.python_file = data.get('python_file', '')
        if not self.repo_remotes:
            self.repo_remotes = data.get('repo_remotes', '')
        if not self.commit:
            self.commit = data.get('commit', '')
        if not self.commit_message:
            self.commit_message = data.get('commit_message', '')
        if self.start_step == None:
            self.start_step = data.get('start_step', '')

        if 'configs' in data:
            self.configs.update(data.get('configs', {}))
        if 'stdout' in data and data['stdout']:
            stdout_processed, self.stdout_unmerged = self.merge_output(self.stdout_unmerged, data['stdout'])
            self.stdout += stdout_processed
        if 'logger' in data and data['logger']:
            logger_processed, self.logger_unmerged = self.merge_output(self.logger_unmerged, data['logger'])
            self.logger += logger_processed
        if 'stderr' in data and data['stderr']:
            stderr_processed, self.stderr_unmerged = self.merge_output(self.stderr_unmerged, data['stderr'])
            self.stderr += stderr_processed

        if not self.indicators:
            self.indicators = data.get('indicators', {})
        if not self.wildcard_indicators:
            self.wildcard_indicators = data.get('wildcard_indicators', {})

        self.save()

    def merge_output(self, unmerged: str, new: str):
        unmerged += new
        processed = ''
        if len(new) > 1:
            processed, unmerged = self.format_output(unmerged)

        return processed, unmerged

    @staticmethod
    def format_output(output: str) -> (str, str):
        res = []
        temp = ''
        for i, c in enumerate(output):
            if c == '\n':
                temp += '\n'
                res.append(temp)
                temp = ''
            elif c == '\r' and len(output) > i + 1 and output[i + 1] == '\n':
                pass
            elif c == '\r':
                temp = ''
            else:
                temp += c

        return ''.join(res), temp

    @staticmethod
    def format_remote_repo(urls: str):
        if not urls:
            return ''

        url = urls[0]

        if not url:
            return ''
        if 'git' not in url:
            logger.error(f'unknown repo url: {url}')
            return ''

        split = url.split(':')

        if split[0] != 'https':
            split[0] = 'https'
            return '://github.com/'.join(split)[:-4]

        return url[:-4]

    @staticmethod
    def format_commit(url: str, commit: str):
        if not url:
            return ''
        if 'unknown' in commit:
            logger.error(f'unknown repo url: {url}, commit:{commit}')
            return 'unknown'

        return url + f'/commit/{commit}'

    def get_data(self) -> Dict[str, Union[str, any]]:
        configs = [{'key': k, **c} for k, c in self.configs.items()]
        formatted_repo = self.format_remote_repo(self.repo_remotes)

        return {
            'run_uuid': self.run_uuid,
            'name': self.name,
            'comment': self.comment,
            'note': self.note,
            'tags': self.tags,
            'start_time': self.start_time,
            'start_step': self.start_step,
            'python_file': self.python_file,
            'repo_remotes': formatted_repo,
            'commit': self.format_commit(formatted_repo, self.commit),
            'commit_message': self.commit_message,
            'is_claimed': self.is_claimed,
            'configs': configs,
            'stdout': self.stdout + self.stdout_unmerged,
            'logger': self.logger + self.logger_unmerged,
            'stderr': self.stderr + self.stderr_unmerged,
        }

    def get_summary(self) -> Dict[str, str]:
        return {
            'run_uuid': self.run_uuid,
            'name': self.name,
            'comment': self.comment,
            'start_time': self.start_time,
        }

    def edit_run(self, data: Dict[str, any]) -> None:
        if 'name' in data:
            self.name = data.get('name', self.name)
        if 'comment' in data:
            self.comment = data.get('comment', self.comment)
        if 'note' in data:
            self.note = data.get('note', self.note)

        self.save()


class RunIndex(Index['Run']):
    pass


def get(run_uuid: str, labml_token: str = '') -> Optional[Run]:
    p = project.get_project(labml_token)

    if run_uuid in p.runs:
        return p.runs[run_uuid].load()
    else:
        return None


def get_or_create(run_uuid: str, labml_token: str = '', run_ip: str = '') -> Run:
    p = project.get_project(labml_token)

    if run_uuid in p.runs:
        return p.runs[run_uuid].load()

    if labml_token == settings.FLOAT_PROJECT_TOKEN:
        is_claimed = False
    else:
        is_claimed = True
        MixPanelEvent.track('run_claimed', {'run_uuid': run_uuid})

    time_now = time.time()

    status = create_status()
    run = Run(run_uuid=run_uuid,
              start_time=time_now,
              run_ip=run_ip,
              is_claimed=is_claimed,
              status=status.key,
              )
    p.runs[run.run_uuid] = run.key
    p.is_run_added = True

    run.save()
    p.save()

    RunIndex.set(run.run_uuid, run.key)

    MixPanelEvent.track('run_created', {'run_uuid': run_uuid,
                                        'run_ip': run_ip,
                                        'labml_token': labml_token}
                        )

    return run


def get_runs(labml_token: str) -> List[Run]:
    res = []
    p = project.get_project(labml_token)
    for run_uuid, run_key in p.runs.items():
        res.append(run_key.load())

    return res


def get_run(run_uuid: str) -> Optional[Run]:
    run_key = RunIndex.get(run_uuid)

    if run_key:
        return run_key.load()

    return None


def get_status(run_uuid: str) -> Union[None, Status]:
    r = get_run(run_uuid)

    if r:
        return r.status.load()

    return None
