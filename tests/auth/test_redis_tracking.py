# -*- encoding: utf-8 -*-
#
# Copyright 2024 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from dci.db import models2
import pytest
import time
import datetime
import uuid
from unittest.mock import patch


@pytest.fixture
def redis_clean(app):
    """Clean Redis database before each test"""
    redis_client = app.redis_client
    if redis_client.is_available():
        # Clear all auth-related keys
        try:
            # Get all auth keys
            keys = redis_client._client.keys("last_auth:*")
            if keys:
                redis_client._client.delete(*keys)
            # Clear the dirty set
            redis_client._client.delete("dirty_last_auth_keys")
            # Clear any sync sets (including failed ones)
            sync_keys = redis_client._client.keys("sync_last_auth_keys:*")
            if sync_keys:
                redis_client._client.delete(*sync_keys)
        except Exception as e:
            pytest.fail(f"Redis cleanup failed: {e}")
    else:
        pytest.fail("Redis is not available")
    return redis_client


def test_basic_auth_tracked_in_redis(client_user1, redis_clean):
    """Test that basic authentication is tracked in Redis"""
    # Perform authentication
    response = client_user1.get("/api/v1/identity")
    assert response.status_code == 200

    # Get user info from response
    identity_data = response.data
    user_id = identity_data["identity"]["id"]

    # Check Redis tracking (redis_clean fixture ensures Redis is available)
    timestamp = redis_clean.get_last_auth("user", user_id)
    assert timestamp is not None
    # Timestamp should be recent (within last 5 seconds)
    assert int(time.time()) - timestamp < 5

    # Verify the key is added to the dirty set
    key = f"last_auth:user:{user_id}"
    assert redis_clean._client.sismember("dirty_last_auth_keys", key) == 1


def test_remoteci_auth_tracked_in_redis(hmac_client_team1, redis_clean):
    """Test that remoteci HMAC authentication is tracked in Redis"""
    # Perform authentication
    response = hmac_client_team1.get("/api/v1/identity")
    assert response.status_code == 200

    # Get remoteci info from response
    identity_data = response.data
    remoteci_id = identity_data["identity"]["id"]

    # Check Redis tracking (redis_clean fixture ensures Redis is available)
    timestamp = redis_clean.get_last_auth("remoteci", remoteci_id)
    assert timestamp is not None
    # Timestamp should be recent (within last 5 seconds)
    assert int(time.time()) - timestamp < 5

    # Verify the key is added to the dirty set
    key = f"last_auth:remoteci:{remoteci_id}"
    assert redis_clean._client.sismember("dirty_last_auth_keys", key) == 1


def test_multiple_auths_update_timestamp(hmac_client_team1, redis_clean):
    """Test that multiple authentications update the timestamp"""
    # First authentication
    response = hmac_client_team1.get("/api/v1/identity")
    assert response.status_code == 200
    remoteci_id = response.data["identity"]["id"]

    timestamp_1 = redis_clean.get_last_auth("remoteci", remoteci_id)
    assert timestamp_1 is not None

    # Verify key is in dirty set after first auth
    key = f"last_auth:remoteci:{remoteci_id}"
    assert redis_clean._client.sismember("dirty_last_auth_keys", key) == 1

    # Wait a bit
    time.sleep(1)

    # Second authentication
    response = hmac_client_team1.get("/api/v1/identity")
    assert response.status_code == 200

    timestamp_2 = redis_clean.get_last_auth("remoteci", remoteci_id)
    assert timestamp_2 is not None

    # Second timestamp should be greater than first
    assert timestamp_2 > timestamp_1

    # Key should still be in dirty set (duplicate adds are handled by set)
    assert redis_clean._client.sismember("dirty_last_auth_keys", key) == 1


def test_auth_tracking_does_not_break_when_redis_unavailable(app, hmac_client_team1):
    """Test that authentication still works even if Redis is unavailable"""
    app.redis_client._client = None
    assert app.redis_client.is_available() is False
    response = hmac_client_team1.get("/api/v1/identity")
    assert response.status_code == 200


def test_redis_fixture_clears_data(client_user1, redis_clean):
    """Test that redis_clean fixture properly clears data between tests"""
    # This test verifies isolation - should not see data from previous tests
    # After cleanup, there should be no auth keys
    keys = redis_clean._client.keys("last_auth:*")
    assert len(keys) == 0, "Redis should be clean at test start"

    # Dirty set should also be empty
    dirty_count = redis_clean._client.scard("dirty_last_auth_keys")
    assert dirty_count == 0, "Dirty set should be empty at test start"

    # Authenticate
    response = client_user1.get("/api/v1/identity")
    assert response.status_code == 200
    user_id = response.data["identity"]["id"]

    # Should now have exactly 1 auth key
    keys = redis_clean._client.keys("last_auth:*")
    assert len(keys) == 1

    # Verify it's the correct user
    timestamp = redis_clean.get_last_auth("user", user_id)
    assert timestamp is not None
    assert isinstance(timestamp, int)

    # Dirty set should now have exactly 1 member
    dirty_count = redis_clean._client.scard("dirty_last_auth_keys")
    assert dirty_count == 1

    # Verify the key is in the dirty set
    key = f"last_auth:user:{user_id}"
    assert redis_clean._client.sismember("dirty_last_auth_keys", key) == 1


def test_dirty_set_tracks_multiple_entities(
    client_user1, hmac_client_team1, redis_clean
):
    """Test that dirty set correctly tracks multiple different entities"""
    # Initially dirty set should be empty
    dirty_count = redis_clean._client.scard("dirty_last_auth_keys")
    assert dirty_count == 0

    # Authenticate as user
    response = client_user1.get("/api/v1/identity")
    assert response.status_code == 200
    user_id = response.data["identity"]["id"]

    # Dirty set should have 1 member
    dirty_count = redis_clean._client.scard("dirty_last_auth_keys")
    assert dirty_count == 1

    # Authenticate as remoteci
    response = hmac_client_team1.get("/api/v1/identity")
    assert response.status_code == 200
    remoteci_id = response.data["identity"]["id"]

    # Dirty set should now have 2 members (user + remoteci)
    dirty_count = redis_clean._client.scard("dirty_last_auth_keys")
    assert dirty_count == 2

    # Verify both keys are in the set
    user_key = f"last_auth:user:{user_id}"
    remoteci_key = f"last_auth:remoteci:{remoteci_id}"
    assert redis_clean._client.sismember("dirty_last_auth_keys", user_key) == 1
    assert redis_clean._client.sismember("dirty_last_auth_keys", remoteci_key) == 1

    # Get all members and verify the set contents
    all_members = redis_clean._client.smembers("dirty_last_auth_keys")
    assert user_key in all_members
    assert remoteci_key in all_members
    assert len(all_members) == 2


def test_sync_dirty_auth_keys_success(
    session, client_user1, hmac_client_team1, redis_clean
):
    """Test successful sync of dirty auth keys to database"""
    # Authenticate to create dirty keys
    user_response = client_user1.get("/api/v1/identity")
    assert user_response.status_code == 200
    user_id = user_response.data["identity"]["id"]

    remoteci_response = hmac_client_team1.get("/api/v1/identity")
    assert remoteci_response.status_code == 200
    remoteci_id = remoteci_response.data["identity"]["id"]

    # Verify dirty set has 2 members
    dirty_count = redis_clean._client.scard("dirty_last_auth_keys")
    assert dirty_count == 2

    # Verify database last_auth_at is None before sync
    user = session.query(models2.User).filter(models2.User.id == user_id).first()
    remoteci = (
        session.query(models2.Remoteci)
        .filter(models2.Remoteci.id == remoteci_id)
        .first()
    )
    assert user.last_auth_at is None
    assert remoteci.last_auth_at is None

    # Perform sync
    stats = redis_clean.sync_dirty_auth_keys(session)

    # Verify sync stats
    assert stats["entities_synced"] == 2
    assert stats["errors"] == 0

    # Verify dirty set is empty after sync
    dirty_count = redis_clean._client.scard("dirty_last_auth_keys")
    assert dirty_count == 0

    # Verify database was updated
    session.expire_all()  # Refresh from database
    user = session.query(models2.User).filter(models2.User.id == user_id).first()
    remoteci = (
        session.query(models2.Remoteci)
        .filter(models2.Remoteci.id == remoteci_id)
        .first()
    )

    assert user.last_auth_at is not None
    assert remoteci.last_auth_at is not None

    # Verify timestamps are recent (within last 10 seconds)
    # Database stores naive UTC datetimes, so make timezone-aware for comparison
    now = datetime.datetime.now(datetime.timezone.utc)
    user_last_auth_aware = user.last_auth_at.replace(tzinfo=datetime.timezone.utc)
    remoteci_last_auth_aware = remoteci.last_auth_at.replace(
        tzinfo=datetime.timezone.utc
    )
    assert (now - user_last_auth_aware).total_seconds() < 10
    assert (now - remoteci_last_auth_aware).total_seconds() < 10


def test_sync_dirty_auth_keys_empty_set(session, redis_clean):
    """Test sync with empty dirty set"""
    # Verify dirty set is empty
    dirty_count = redis_clean._client.scard("dirty_last_auth_keys")
    assert dirty_count == 0

    # Perform sync
    stats = redis_clean.sync_dirty_auth_keys(session)

    # Verify stats show no work done
    assert stats["entities_synced"] == 0
    assert stats["errors"] == 0


def test_sync_dirty_auth_keys_preserves_failed_sync(session, client_user1, redis_clean):
    """Test that failed sync preserves data in failed set"""
    # Authenticate to create dirty keys
    user_response = client_user1.get("/api/v1/identity")
    assert user_response.status_code == 200
    user_id = user_response.data["identity"]["id"]

    # Verify dirty set has 1 member
    dirty_count = redis_clean._client.scard("dirty_last_auth_keys")
    assert dirty_count == 1

    # Force a database error by mocking session.commit to raise an exception
    with patch.object(
        session, "commit", side_effect=Exception("Database commit failed")
    ):
        # Perform sync (should fail due to commit error)
        stats = redis_clean.sync_dirty_auth_keys(session)

    # Verify errors were recorded
    assert stats["errors"] > 0

    # Verify dirty set is still empty (renamed to failed)
    dirty_count = redis_clean._client.scard("dirty_last_auth_keys")
    assert dirty_count == 0

    # Verify failed set exists and contains the data
    failed_sets = redis_clean._client.keys("sync_last_auth_keys:failed:*")
    assert len(failed_sets) == 1

    # Verify the failed set contains the expected key
    failed_set_name = failed_sets[0]
    failed_members = redis_clean._client.smembers(failed_set_name)
    assert len(failed_members) == 1
    assert f"last_auth:user:{user_id}" in failed_members

    # Clean up failed set
    redis_clean._client.delete(failed_set_name)


def test_fetch_auth_updates_from_redis(redis_clean):
    """Test _fetch_auth_updates_from_redis method"""
    # Create test data in Redis
    test_timestamp = int(time.time())
    test_user_id = str(uuid.uuid4())
    test_remoteci_id = str(uuid.uuid4())

    sync_set_name = "test_sync_set"

    # Add keys to sync set and set their values
    user_key = f"last_auth:user:{test_user_id}"
    remoteci_key = f"last_auth:remoteci:{test_remoteci_id}"

    redis_clean._client.sadd(sync_set_name, user_key, remoteci_key)
    redis_clean._client.set(user_key, test_timestamp)
    redis_clean._client.set(remoteci_key, test_timestamp)

    # Fetch updates
    updates_by_type, error_count = redis_clean._fetch_auth_updates_from_redis(
        sync_set_name
    )

    # Verify results
    assert error_count == 0
    assert len(updates_by_type["user"]) == 1
    assert len(updates_by_type["remoteci"]) == 1
    assert len(updates_by_type["feeder"]) == 0

    # Verify user update
    user_update = updates_by_type["user"][0]
    assert user_update["id"] == uuid.UUID(test_user_id)
    assert isinstance(user_update["last_auth_at"], datetime.datetime)

    # Verify remoteci update
    remoteci_update = updates_by_type["remoteci"][0]
    assert remoteci_update["id"] == uuid.UUID(test_remoteci_id)
    assert isinstance(remoteci_update["last_auth_at"], datetime.datetime)

    # Clean up
    redis_clean._client.delete(sync_set_name, user_key, remoteci_key)


def test_fetch_auth_updates_handles_invalid_keys(redis_clean):
    """Test _fetch_auth_updates_from_redis handles invalid keys gracefully"""
    sync_set_name = "test_sync_set_invalid"

    # Add invalid keys
    redis_clean._client.sadd(sync_set_name, "invalid_key")
    redis_clean._client.sadd(sync_set_name, "last_auth:invalid_type:123")
    redis_clean._client.sadd(sync_set_name, "last_auth:user:not-a-uuid")

    redis_clean._client.set("invalid_key", "123456")
    redis_clean._client.set("last_auth:invalid_type:123", "123456")
    redis_clean._client.set("last_auth:user:not-a-uuid", "123456")

    # Fetch updates
    updates_by_type, error_count = redis_clean._fetch_auth_updates_from_redis(
        sync_set_name
    )

    # Verify all keys were rejected with errors
    assert error_count == 3
    assert len(updates_by_type["user"]) == 0
    assert len(updates_by_type["remoteci"]) == 0
    assert len(updates_by_type["feeder"]) == 0

    # Clean up
    redis_clean._client.delete(
        sync_set_name,
        "invalid_key",
        "last_auth:invalid_type:123",
        "last_auth:user:not-a-uuid",
    )


def test_update_database_auth_timestamps(session, admin, team1_remoteci, redis_clean):
    """Test _update_database_auth_timestamps method"""
    # Get the actual database objects
    admin_id = admin["id"]
    remoteci_id = team1_remoteci["id"]

    user_obj = session.query(models2.User).filter(models2.User.id == admin_id).first()
    remoteci_obj = (
        session.query(models2.Remoteci)
        .filter(models2.Remoteci.id == remoteci_id)
        .first()
    )

    # Verify initial state
    assert user_obj.last_auth_at is None
    assert remoteci_obj.last_auth_at is None

    # Prepare updates - use naive UTC datetime to match database convention
    test_datetime = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    updates_by_type = {
        "user": [{"id": admin_id, "last_auth_at": test_datetime}],
        "remoteci": [{"id": remoteci_id, "last_auth_at": test_datetime}],
        "feeder": [],
    }

    # Update database
    entities_synced, error_count = redis_clean._update_database_auth_timestamps(
        session, updates_by_type
    )

    # Commit the changes
    session.commit()

    # Verify results
    assert entities_synced == 2
    assert error_count == 0

    # Refresh from database
    session.expire_all()
    user = session.query(models2.User).filter(models2.User.id == admin_id).first()
    remoteci = (
        session.query(models2.Remoteci)
        .filter(models2.Remoteci.id == remoteci_id)
        .first()
    )

    # Verify timestamps were updated
    assert user.last_auth_at is not None
    assert remoteci.last_auth_at is not None
    # Compare timestamps (allowing small difference due to microseconds)
    assert abs((user.last_auth_at - test_datetime).total_seconds()) < 1
    assert abs((remoteci.last_auth_at - test_datetime).total_seconds()) < 1


def test_sync_multiple_authentications_same_entity(session, client_user1, redis_clean):
    """Test that multiple authentications of same entity only creates one update"""
    # Authenticate multiple times
    for _ in range(3):
        response = client_user1.get("/api/v1/identity")
        assert response.status_code == 200
        time.sleep(0.1)

    user_id = client_user1.get("/api/v1/identity").data["identity"]["id"]

    # Dirty set should still have only 1 member (set deduplication)
    dirty_count = redis_clean._client.scard("dirty_last_auth_keys")
    assert dirty_count == 1

    # Sync
    stats = redis_clean.sync_dirty_auth_keys(session)

    # Should sync 1 entity
    assert stats["entities_synced"] == 1
    assert stats["errors"] == 0

    # Verify database has the latest timestamp
    session.expire_all()
    user = session.query(models2.User).filter(models2.User.id == user_id).first()
    assert user.last_auth_at is not None


def test_cardinality_check(redis_clean):
    """Test cardinality check using scard"""
    # Initial cardinality should be 0
    cardinality = redis_clean._client.scard("dirty_last_auth_keys")
    assert cardinality == 0

    # Add some keys manually
    redis_clean._client.sadd("dirty_last_auth_keys", "key1", "key2", "key3")

    # Check cardinality
    cardinality = redis_clean._client.scard("dirty_last_auth_keys")
    assert cardinality == 3

    # Clean up
    redis_clean._client.delete("dirty_last_auth_keys")
