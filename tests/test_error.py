from sqlalchemy.exc import IntegrityError

def test_database_error(logged_in_client, mocker):

    mocker.patch(
        "models.session.commit",
        side_effect=IntegrityError(
            "INSERT INTO clients",
            {},
            Exception("Duplicate key")
        )
    )

    rollback_mock = mocker.patch(
        "models.session.rollback"
    )

    response = logged_in_client.post(
        "/admin/",
        data={"client": "テストクライアント"}
    )

    assert response.status_code == 500
    rollback_mock.assert_called_once()
