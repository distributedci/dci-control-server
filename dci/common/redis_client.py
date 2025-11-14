# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import datetime
import logging
import time
import uuid

import redis

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for tracking authentication events."""

    def __init__(self, redis_url):
        """Initialize Redis client with connection URL.

        Args:
            redis_url: Redis connection string (e.g., redis://localhost:6379/0)
        """
        self.redis_url = redis_url
        self._client = None

        if redis_url:
            try:
                self._client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self._client.ping()
                logger.info(f"Redis client initialized successfully: {redis_url}")
            except Exception as e:
                logger.warning(
                    f"Failed to connect to Redis: {e}, authentication tracking disabled"
                )
                self._client = None

    def is_available(self):
        """Check if Redis client is available and connected."""
        return self._client is not None

    def track_authentication(self, identity):
        """Track authentication event for a user or remoteci.

        Args:
            identity: Identity object containing user/remoteci information
        """
        if not self.is_available():
            return

        try:
            # Get current UTC timestamp (seconds since Unix epoch)
            timestamp = int(time.time())
            entity_id = identity.id

            # Determine entity type
            if identity.is_remoteci():
                entity_type = "remoteci"
            elif identity.is_user():
                entity_type = "user"
            elif identity.is_feeder():
                entity_type = "feeder"
            else:
                entity_type = "unknown"

            # Store in Redis with key format: last_auth:{type}:{id}
            key = f"last_auth:{entity_type}:{entity_id}"

            # Store timestamp as simple string value
            self._client.set(key, timestamp)

            # Add key to dirty set for tracking changes
            self._client.sadd("dirty_last_auth_keys", key)

            logger.debug(
                f"Tracked authentication: {entity_type}={entity_id} at {timestamp}"
            )

        except Exception as e:
            # Don't fail authentication if Redis tracking fails
            logger.warning(f"Failed to track authentication in Redis: {e}")

    def get_last_auth(self, entity_type, entity_id):
        """Get last authentication timestamp for an entity.

        Args:
            entity_type: Type of entity (user, remoteci, feeder)
            entity_id: ID of the entity

        Returns:
            Integer timestamp or None if not found
        """
        if not self.is_available():
            return None

        try:
            key = f"last_auth:{entity_type}:{entity_id}"
            timestamp = self._client.get(key)
            return int(timestamp) if timestamp else None
        except Exception as e:
            logger.warning(f"Failed to get last auth from Redis: {e}")
            return None

    def _fetch_auth_updates_from_redis(self, sync_set_name):
        """Fetch authentication updates from Redis sync set.

        Args:
            sync_set_name: Name of the Redis set containing keys to sync

        Returns:
            Tuple of (updates_by_type dict, error_count int)
        """
        error_count = 0
        updates_by_type = {
            "user": [],
            "remoteci": [],
            "feeder": [],
        }

        # Get all members from the sync set
        sync_keys = list(self._client.smembers(sync_set_name))
        logger.info(f"Fetching {len(sync_keys)} authentication records from Redis")

        if not sync_keys:
            return updates_by_type, error_count

        # Fetch all timestamp values at once using mget
        timestamp_values = self._client.mget(sync_keys)

        # Parse all keys and group by entity type
        for key, timestamp_str in zip(sync_keys, timestamp_values):
            try:
                # Parse key format: last_auth:{type}:{id}
                parts = key.split(":")
                if len(parts) != 3 or parts[0] != "last_auth":
                    logger.warning(f"Invalid key format: {key}")
                    error_count += 1
                    continue

                entity_type = parts[1]
                entity_id = parts[2]

                if entity_type not in updates_by_type:
                    logger.warning(f"Unknown entity type: {entity_type}")
                    error_count += 1
                    continue

                # Check if timestamp value exists
                if not timestamp_str:
                    logger.warning(f"No timestamp found for key: {key}")
                    error_count += 1
                    continue

                # Convert Unix timestamp to datetime
                # Note: Using naive UTC datetime to match database column convention
                auth_datetime = datetime.datetime.fromtimestamp(
                    int(timestamp_str), tz=datetime.timezone.utc
                ).replace(tzinfo=None)

                # Add to updates for this entity type
                try:
                    updates_by_type[entity_type].append(
                        {"id": uuid.UUID(entity_id), "last_auth_at": auth_datetime}
                    )
                except ValueError:
                    logger.warning(f"Invalid UUID for {entity_type}: {entity_id}")
                    error_count += 1
                    continue

            except Exception as e:
                logger.error(f"Error processing key {key}: {e}")
                error_count += 1

        return updates_by_type, error_count

    def _update_database_auth_timestamps(self, session, updates_by_type):
        """Update database with authentication timestamps.

        Args:
            session: SQLAlchemy database session
            updates_by_type: Dictionary mapping entity type to list of updates

        Returns:
            Tuple of (entities_synced count, error_count)
        """
        # Import here to avoid circular dependencies
        from dci.db import models2
        from sqlalchemy import update, bindparam

        entities_synced = 0
        error_count = 0

        # Perform bulk updates for each entity type
        model_map = {
            "user": models2.User,
            "remoteci": models2.Remoteci,
            "feeder": models2.Feeder,
        }

        for entity_type, updates in updates_by_type.items():
            if not updates:
                continue

            model = model_map[entity_type]
            logger.info(f"Updating {len(updates)} {entity_type} records in database")

            try:
                # Bulk update using session.execute with bindparam
                # Note: 'b_id' is used instead of 'id' because 'id' is reserved by SQLAlchemy
                session.execute(
                    update(model).where(model.id == bindparam("b_id")),
                    [
                        {"b_id": u["id"], "last_auth_at": u["last_auth_at"]}
                        for u in updates
                    ],
                )
                entities_synced += len(updates)
                logger.info(
                    f"Successfully updated {len(updates)} {entity_type} records"
                )

            except Exception as e:
                logger.error(f"Failed to bulk update {entity_type} records: {e}")
                error_count += len(updates)

        return entities_synced, error_count

    def sync_dirty_auth_keys(self, session):
        """Sync dirty authentication keys from Redis to database.

        This method atomically renames the dirty_last_auth_keys set to a timestamped
        sync set, fetches data from Redis, updates the database with all authentication
        timestamps using bulk updates, and then removes the sync set.

        The sync is performed in two phases:
        1. Database phase: Rename, fetch, update, and commit (atomic with rollback)
        2. Cleanup phase: Delete sync set (best-effort, DB already committed)

        Args:
            session: SQLAlchemy database session for updating records

        Returns:
            Dictionary with sync statistics (entities_synced, errors)
        """
        if not self.is_available():
            logger.warning("Redis not available, skipping auth keys sync")
            return {"entities_synced": 0, "errors": 0}

        # Get current UTC timestamp
        sync_timestamp = int(time.time())
        sync_set_name = f"sync_last_auth_keys:{sync_timestamp}"
        dirty_set_name = "dirty_last_auth_keys"

        stats = {"entities_synced": 0, "errors": 0}

        # Phase 1: Database update (atomic with rollback on failure)
        try:
            # Atomically rename the dirty set to sync set
            # This ensures we don't lose any new authentications that happen during sync
            try:
                self._client.rename(dirty_set_name, sync_set_name)
                # Set TTL as safety net in case cleanup fails (24 hours)
                self._client.expire(sync_set_name, 86400)
            except Exception as e:
                # Key might not exist if there are no dirty keys
                if "no such key" in str(e).lower():
                    logger.info("No dirty auth keys to sync")
                    return stats
                raise

            # Fetch authentication updates from Redis
            updates_by_type, fetch_errors = self._fetch_auth_updates_from_redis(
                sync_set_name
            )
            stats["errors"] += fetch_errors

            # Check if there's anything to update
            total_updates = sum(len(updates) for updates in updates_by_type.values())
            if total_updates == 0:
                logger.info("No valid updates to sync to database")
                self._client.delete(sync_set_name)
                return stats

            # Update database with authentication timestamps
            entities_synced, db_errors = self._update_database_auth_timestamps(
                session, updates_by_type
            )
            stats["entities_synced"] += entities_synced
            stats["errors"] += db_errors

            # Commit all database changes (point of no return)
            session.commit()
            logger.info(
                f"Database committed: {stats['entities_synced']} entities updated, "
                f"{stats['errors']} errors"
            )

        except Exception as e:
            # Database phase failed - rollback and preserve data for retry
            session.rollback()
            logger.error(f"Database sync failed, rolling back: {e}")
            stats["errors"] += 1

            # Preserve sync set as failed for later inspection/retry
            failed_set_name = f"sync_last_auth_keys:failed:{sync_timestamp}"
            try:
                self._client.rename(sync_set_name, failed_set_name)
                # Set longer TTL on failed sets for manual inspection (7 days)
                self._client.expire(failed_set_name, 604800)
                logger.error(
                    f"Sync failed, data preserved in Redis set: {failed_set_name}"
                )
            except Exception as rename_error:
                logger.error(
                    f"Failed to preserve sync set after failure: {rename_error}"
                )

            return stats

        # Phase 2: Cleanup Redis sync set (best-effort, DB already committed)
        try:
            self._client.delete(sync_set_name)
            logger.info("Redis sync set cleaned up successfully")
        except Exception as e:
            # Database is already updated, so this is just a cleanup warning
            # The sync set will be automatically cleaned up by TTL after 24 hours
            logger.warning(
                f"Failed to cleanup Redis sync set {sync_set_name}: {e}. "
                f"Data was successfully synced to database. "
                f"Set will expire automatically after 24 hours."
            )
            # Don't increment error count - sync was actually successful

        return stats
