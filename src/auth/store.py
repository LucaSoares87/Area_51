from __future__ import annotations

import json
import threading
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from src.auth.models import ApiKey, Role, User

T = TypeVar("T")


class BaseStore(ABC, Generic[T]):
    def __init__(
        self,
        store_dir: str | Path,
        filename: str,
    ) -> None:
        self._store_dir = Path(store_dir)
        self._store_dir.mkdir(parents=True, exist_ok=True)
        self._filepath = self._store_dir / filename
        self._lock = threading.Lock()
        self._data: dict[str, T] = {}
        self._load()

    @property
    def filepath(self) -> Path:
        return self._filepath

    @abstractmethod
    def _serialize_item(self, item: T) -> dict[str, Any]: ...

    @abstractmethod
    def _deserialize_item(self, data: dict[str, Any]) -> T: ...

    @abstractmethod
    def _collection_key(self) -> str: ...

    @abstractmethod
    def _extract_key(self, item: T) -> str: ...

    def _get(self, key: str) -> T | None:
        return self._data.get(key)

    def _put(self, key: str, item: T) -> None:
        with self._lock:
            self._data[key] = item
            self._save()

    def _remove(self, key: str) -> bool:
        with self._lock:
            if key not in self._data:
                return False

            del self._data[key]
            self._save()
            return True

    def _remove_where(self, predicate: Any) -> int:
        with self._lock:
            keys = [key for key, value in self._data.items() if predicate(value)]

            for key in keys:
                del self._data[key]

            if keys:
                self._save()

        return len(keys)

    def _all_items(self) -> list[T]:
        with self._lock:
            return list(self._data.values())

    def _filter(self, predicate: Any) -> list[T]:
        return [value for value in self._all_items() if predicate(value)]

    def _count(self) -> int:
        return len(self._data)

    def _exists(self, key: str) -> bool:
        return key in self._data

    def _clear(self) -> None:
        with self._lock:
            self._data.clear()
            self._save()

    def _load(self) -> None:
        if not self._filepath.exists():
            return

        try:
            raw = self._filepath.read_text(encoding="utf-8")
            payload = json.loads(raw)

            for entry in payload.get(self._collection_key(), []):
                item = self._deserialize_item(entry)
                key = self._extract_key(item)
                self._data[key] = item
        except (json.JSONDecodeError, KeyError, ValueError):
            self._data = {}

    def _save(self) -> None:
        payload = {
            "version": 1,
            "updated_at": datetime.now(UTC).isoformat(),
            self._collection_key(): [
                self._serialize_item(item) for item in self._data.values()
            ],
        }

        self._filepath.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


class ApiKeyJsonStore(BaseStore[ApiKey]):
    DEFAULT_DIR = Path("data/auth")
    DEFAULT_FILENAME = "api_keys.json"

    def __init__(
        self,
        store_dir: str | Path | None = None,
        filename: str = DEFAULT_FILENAME,
    ) -> None:
        from src.auth.models import ApiKey

        self._ApiKey = ApiKey

        super().__init__(
            store_dir=store_dir or self.DEFAULT_DIR,
            filename=filename,
        )

    def _collection_key(self) -> str:
        return "keys"

    def _serialize_item(self, item: ApiKey) -> dict[str, Any]:
        return item.to_dict()

    def _deserialize_item(self, data: dict[str, Any]) -> ApiKey:
        return self._ApiKey.from_dict(data)

    def _extract_key(self, item: ApiKey) -> str:
        return item.key_hash

    def put(self, api_key: ApiKey) -> None:
        self._put(api_key.key_hash, api_key)

    def get(self, key_hash: str) -> ApiKey | None:
        return self._get(key_hash)

    def remove(self, key_hash: str) -> bool:
        return self._remove(key_hash)

    def all(self) -> list[ApiKey]:
        return self._all_items()

    def active(self) -> list[ApiKey]:
        return self._filter(lambda key: key.is_usable)

    def count(self) -> int:
        return self._count()

    def exists(self, key_hash: str) -> bool:
        return self._exists(key_hash)

    def clear(self) -> None:
        self._clear()

    def remove_revoked(self) -> int:
        from src.auth.models import KeyStatus

        return self._remove_where(lambda key: key.status == KeyStatus.REVOKED)

    def save(self) -> None:
        with self._lock:
            self._save()


class SessionJsonStore(BaseStore[dict[str, Any]]):
    DEFAULT_DIR = Path("data/auth")
    DEFAULT_FILENAME = "sessions.json"

    def __init__(
        self,
        store_dir: str | Path | None = None,
        filename: str = DEFAULT_FILENAME,
    ) -> None:
        super().__init__(
            store_dir=store_dir or self.DEFAULT_DIR,
            filename=filename,
        )

    def _collection_key(self) -> str:
        return "sessions"

    def _serialize_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return item

    def _deserialize_item(self, data: dict[str, Any]) -> dict[str, Any]:
        return data

    def _extract_key(self, item: dict[str, Any]) -> str:
        return item["session_id"]

    def create(
        self,
        session_id: str,
        key_hash: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session = {
            "session_id": session_id,
            "key_hash": key_hash,
            "created_at": datetime.now(UTC).isoformat(),
            "last_activity": datetime.now(UTC).isoformat(),
            "active": True,
            "metadata": metadata or {},
        }

        self._put(session_id, session)
        return session

    def get(self, session_id: str) -> dict[str, Any] | None:
        return self._get(session_id)

    def touch(self, session_id: str) -> bool:
        with self._lock:
            session = self._data.get(session_id)

            if session is None:
                return False

            session["last_activity"] = datetime.now(UTC).isoformat()
            self._save()

        return True

    def invalidate(self, session_id: str) -> bool:
        with self._lock:
            session = self._data.get(session_id)

            if session is None:
                return False

            session["active"] = False
            self._save()

        return True

    def invalidate_by_key(self, key_hash: str) -> int:
        count = 0

        with self._lock:
            for session in self._data.values():
                if session.get("key_hash") == key_hash and session.get("active"):
                    session["active"] = False
                    count += 1

            if count > 0:
                self._save()

        return count

    def get_active(self) -> list[dict[str, Any]]:
        return self._filter(lambda session: session.get("active", False))

    def remove(self, session_id: str) -> bool:
        return self._remove(session_id)

    def remove_inactive(self) -> int:
        return self._remove_where(lambda session: not session.get("active", False))

    def all(self) -> list[dict[str, Any]]:
        return self._all_items()

    def count(self) -> int:
        return self._count()

    def clear(self) -> None:
        self._clear()


class UserJsonStore(BaseStore[User]):
    DEFAULT_DIR = Path("data/auth")
    DEFAULT_FILENAME = "users.json"

    def __init__(
        self,
        store_dir: str | Path | None = None,
        filename: str = DEFAULT_FILENAME,
    ) -> None:
        from src.auth.models import User

        self._User = User

        super().__init__(
            store_dir=store_dir or self.DEFAULT_DIR,
            filename=filename,
        )

    def _collection_key(self) -> str:
        return "users"

    def _serialize_item(self, item: User) -> dict[str, Any]:
        return item.to_dict()

    def _deserialize_item(self, data: dict[str, Any]) -> User:
        return self._User.from_dict(data)

    def _extract_key(self, item: User) -> str:
        return item.username

    def create(
        self,
        username: str,
        email: str,
        full_name: str,
        hashed_password: str,
        role: Role | None = None,
    ) -> User:
        from src.auth.models import Role as RoleEnum

        if role is None:
            role = RoleEnum.VIEWER

        user = self._User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
        )

        self._put(user.username, user)
        return user

    def put(self, user: User) -> None:
        self._put(user.username, user)

    def get_by_username(self, username: str) -> User | None:
        return self._get(username)

    def get_by_email(self, email: str) -> User | None:
        results = self._filter(lambda user: user.email == email)
        return results[0] if results else None

    def all(self) -> list[User]:
        return self._all_items()

    def remove(self, username: str) -> bool:
        return self._remove(username)

    def exists(self, username: str) -> bool:
        return self._exists(username)

    def count(self) -> int:
        return self._count()

    def clear(self) -> None:
        self._clear()


user_store = UserJsonStore()