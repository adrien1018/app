from uuid import uuid4
from typing import List, NamedTuple, Dict, Union

from labml_db import Model, Key, Index

from .run import Run


def generate_token() -> str:
    return uuid4().hex


class Project(Model['Project']):
    labml_token: str
    is_sharable: str
    name: str
    runs: Dict[str, Key[Run]]

    @classmethod
    def defaults(cls):
        return dict(name='',
                    is_sharable=False,
                    labml_token=generate_token(),
                    runs=[]
                    )

    def get_runs(self) -> List:
        res = []
        for run_uuid, run_key in self.runs.items():
            res.append(run_key.load())

        return res


class ProjectIndex(Index['Project']):
    pass


class User(Model['User']):
    name: str
    sub: str
    email: str
    picture: str
    email_verified: bool
    projects: List[Key[Project]]

    @classmethod
    def defaults(cls):
        return dict(name='',
                    sub='',
                    email='',
                    picture='',
                    email_verified=False,
                    projects=[]
                    )

    @property
    def default_project(self):
        return self.projects[0].load()


class UserIndex(Index['User']):
    pass


class AuthOInfo(NamedTuple):
    name: str
    sub: str
    email: str
    picture: str
    email_verified: bool


def get_or_create_user(info: AuthOInfo) -> User:
    user_key = UserIndex.get(info.email)

    if not user_key:
        project = Project()
        user = User(name=info.name,
                    sub=info.sub,
                    email=info.email,
                    picture=info.picture,
                    email_verified=info.email_verified,
                    projects=[project.key]
                    )

        user.save()
        project.save()

        UserIndex.set(user.email, user.key)
        ProjectIndex.set(project.labml_token, project.key)

        return user

    return user_key.load()


def get_project(labml_token: str) -> Union[None, Project]:
    project_key = ProjectIndex.get(labml_token)

    if project_key:
        return project_key.load()

    return None
