from datetime import datetime, timedelta
from types import SimpleNamespace

from app.backend.repositories.crashed_container_repository import CrashedContainerRepository
from app.backend.repositories.user_repository import UserRepository
from app.backend.schemas.crashed_container_schema import CrashedContainerBase
from app.backend.models.user import User


def test_add_and_get_crashed_containers(logger):
    ct = CrashedContainerBase(container_id="c1", container_name="cont1", logs="log1")
    added = CrashedContainerRepository.add_crashed_container(ct, logger)
    assert added.container_id == "c1"

    date_from = datetime.now() - timedelta(days=1)
    date_to = datetime.now() + timedelta(days=1)
    allc = CrashedContainerRepository.get_all_crashed_containers(date_from, date_to)
    assert len(allc) == 1
    assert allc[0].container_id == "c1"


def test_get_stats_grouping(logger):
    # add two crashes for the same container
    ct1 = CrashedContainerBase(container_id="c2", container_name="cont2", logs="l1")
    ct2 = CrashedContainerBase(container_id="c2", container_name="cont2", logs="l2")
    CrashedContainerRepository.add_crashed_container(ct1, logger)
    CrashedContainerRepository.add_crashed_container(ct2, logger)

    date_from = datetime.now() - timedelta(days=1)
    date_to = datetime.now() + timedelta(days=1)
    stats = CrashedContainerRepository.get_crashed_containers_stats_by_date(date_from, date_to)

    assert any(s.container_id == "c2" and s.crash_count >= 2 for s in stats)


def test_user_get_and_update(logger):
    # create a new user directly using the test SessionLocal
    from app.backend.core.database import SessionLocal
    with SessionLocal() as db:
        u = User(username="u1", password="p1", createdon=datetime.now().date())
        db.add(u)
        db.commit()
        db.refresh(u)
        uid = u.id

    got = UserRepository.get_user(uid)
    assert got is not None and got.username == "u1"

    # update user
    user_obj = SimpleNamespace(id=uid, username="u1_updated", password="p2")
    updated = UserRepository.update_user(user_obj, logger)
    assert updated is not None and updated.username == "u1_updated"

    # update non-existent user
    missing = SimpleNamespace(id=9999, username="x", password="p")
    res = UserRepository.update_user(missing, logger)
    assert res is None
