"""Публикация манифестов."""
import logging
import uuid
from datetime import datetime
from typing import Optional

from ..services.llm import OpenRouterClient
from ..services.vk import VKClient
from ..storage.database import Database
from ..storage.models import Manifest, Monologue
from ..core.state import StateManager

logger = logging.getLogger(__name__)


class ManifestGenerator:
    """Генератор и публикатор манифестов."""

    def __init__(
        self,
        llm_client: OpenRouterClient,
        vk_client: VKClient,
        database: Database,
        state_manager: StateManager
    ):
        """Инициализация генератора."""
        self.llm = llm_client
        self.vk = vk_client
        self.db = database
        self.state = state_manager

    def generate_from_monologues(self, monologues: list[Monologue]) -> Optional[Manifest]:
        """Сгенерировать манифест из монологов."""
        if not monologues:
            logger.warning("No monologues to generate manifest from")
            return None

        # Собрать все мысли из монологов
        all_thoughts = []
        for monologue in monologues:
            all_thoughts.extend(monologue.thoughts)

        # Генерировать манифест
        state_context = self.state.get_state_context()
        content = self.llm.generate_manifest(all_thoughts, state_context)

        if not content:
            logger.error("Failed to generate manifest content")
            return None

        manifest = Manifest(
            manifest_id=str(uuid.uuid4()),
            content=content,
            published=False,
            timestamp=datetime.now()
        )

        self.db.save_manifest(manifest)
        return manifest

    def publish_next(self) -> bool:
        """Опубликовать следующий неопубликованный манифест."""
        manifests = self.db.get_unpublished_manifests()

        if not manifests:
            logger.info("No manifests to publish")
            return False

        manifest = manifests[0]  # Самый старый

        # Публикация в VK
        post_id = self.vk.post_message(manifest.content)

        if post_id:
            manifest.published = True
            manifest.published_at = datetime.now()
            self.db.save_manifest(manifest)

            # Частично сбросить состояние
            self.state.reset_after_publication()

            logger.info(f"Published manifest {manifest.manifest_id} as post {post_id}")
            return True
        else:
            logger.error(f"Failed to publish manifest {manifest.manifest_id}")
            return False


