import datetime
import mock

from dci.db import models2


@mock.patch("dci.api.v1.components.get_file_info", return_value={"size": 7})
def test_get_component_file_save_total_downloaded_in_db(
    _,
    admin,
    remoteci_context,
    team_user,
    rhel_80_component,
):
    r = remoteci_context.get(
        "/api/v1/components/%s/files/.composeinfo" % rhel_80_component["id"]
    )
    assert r.status_code == 302

    partner_download_statistics = admin.get("/api/v1/partner_download_statistics").data
    assert len(partner_download_statistics["downloads"]) == 1
    team_user_stats = partner_download_statistics["downloads"][0]
    assert team_user_stats["team_id"] == team_user["id"]
    assert team_user_stats["total_downloaded"] == 7.0


@mock.patch("dci.api.v1.components.get_file_info", return_value={"size": 7})
def test_get_component_file_twice_increment_the_total_downloaded(
    _,
    admin,
    remoteci_context,
    rhel_80_component,
):
    r = remoteci_context.get(
        "/api/v1/components/%s/files/.composeinfo" % rhel_80_component["id"]
    )
    assert r.status_code == 302

    r = remoteci_context.get(
        "/api/v1/components/%s/files/.composeinfo" % rhel_80_component["id"]
    )
    assert r.status_code == 302

    partner_download_statistics = admin.get("/api/v1/partner_download_statistics").data
    assert partner_download_statistics["downloads"][0]["total_downloaded"] == 14.0


def test_get_component_file_between_two_dates_filter_info(
    session, admin, rhel_80_component, team_user
):
    session.add(
        models2.DailyDownload(
            team_id=team_user["id"],
            component_id=rhel_80_component["id"],
            day=datetime.date(2024, 7, 8),
            total_downloaded=100,
        )
    )
    session.add(
        models2.DailyDownload(
            team_id=team_user["id"],
            component_id=rhel_80_component["id"],
            day=datetime.date(2024, 7, 10),
            total_downloaded=100,
        )
    )
    session.commit()
    partner_download_statistics = admin.get("/api/v1/partner_download_statistics").data
    assert partner_download_statistics["downloads"][0]["total_downloaded"] == 200
    partner_download_statistics = admin.get(
        "/api/v1/partner_download_statistics?from=2024-07-07T00:00:00&to=2024-07-09T00:00:00"
    ).data
    assert partner_download_statistics["downloads"][0]["total_downloaded"] == 100
