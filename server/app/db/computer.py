import time
from typing import Dict, List, Optional, Union

from labml_db import Model, Key, Index

from . import project
from .status import create_status, Status
from .. import settings


class Computer(Model['Computer']):
    name: str
    comment: str
    start_time: float
    computer_ip: str
    computer_uuid: str
    session_uuid: str
    is_claimed: bool
    status: Key[Status]
    configs: Dict[str, any]
    errors: List[Dict[str, str]]

    @classmethod
    def defaults(cls):
        return dict(name='',
                    comment='',
                    start_time=None,
                    computer_uuid='',
                    session_uuid='',
                    is_claimed=True,
                    computer_ip='',
                    status=None,
                    configs={},
                    errors=[]
                    )

    @property
    def url(self) -> str:
        return f'{settings.WEB_URL}/session?uuid={self.session_uuid}'

    def update_computer(self, data: Dict[str, any]) -> None:
        if not self.name:
            self.name = data.get('name', '')
        if not self.comment:
            self.comment = data.get('comment', '')
        if 'configs' in data:
            self.configs.update(data.get('configs', {}))

        self.save()

    def get_data(self) -> Dict[str, Union[str, any]]:
        return {
            'computer_uuid': self.computer_uuid,
            'session_uuid': self.session_uuid,
            'name': self.name,
            'comment': self.comment,
            'start_time': self.start_time,
            'configs': [],
        }

    def get_summary(self) -> Dict[str, str]:
        return {
            'computer_uuid': self.computer_uuid,
            'session_uuid': self.session_uuid,
            'name': self.name,
            'comment': self.comment,
            'start_time': self.start_time,
        }


class ComputerIndex(Index['Computer']):
    pass


def get(session_uuid: str, labml_token: str = '') -> Optional[Computer]:
    p = project.get_project(labml_token)

    if session_uuid in p.computers:
        return p.computers[session_uuid].load()
    else:
        return None


def get_or_create(session_uuid: str, computer_uuid: str, labml_token: str = '', computer_ip: str = '') -> Computer:
    p = project.get_project(labml_token)

    if session_uuid in p.computers:
        return p.computers[session_uuid].load()

    is_claimed = True
    if labml_token == settings.FLOAT_PROJECT_TOKEN:
        is_claimed = False

    time_now = time.time()

    status = create_status()
    computer = Computer(session_uuid=session_uuid,
                        computer_uuid=computer_uuid,
                        start_time=time_now,
                        computer_ip=computer_ip,
                        is_claimed=is_claimed,
                        status=status.key,
                        )
    p.computers[computer.session_uuid] = computer.key

    computer.save()
    p.save()

    ComputerIndex.set(computer.session_uuid, computer.key)

    return computer


def get_computers(labml_token: str) -> List[Computer]:
    res = []
    p = project.get_project(labml_token)
    for session_uuid, computer_key in p.computers.items():
        res.append(computer_key.load())

    return res


def get_computer(session_uuid: str) -> Optional[Computer]:
    computer_key = ComputerIndex.get(session_uuid)

    if computer_key:
        return computer_key.load()

    return None


def get_status(session_uuid: str) -> Union[None, Status]:
    c = get_computer(session_uuid)

    if c:
        return c.status.load()

    return None
