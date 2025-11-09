from fastapi import status


def test_employee_workflow(api_client, golden_employee):
    admin_creds = ("admin", golden_employee["users"]["admin"]["password"])
    analyst_creds = ("analyst", golden_employee["users"]["analyst"]["password"])
    emp_no = golden_employee["employee"]["emp_no"]
    original_last = golden_employee["employee"]["last_name"]

    response = api_client.post("/sessions/start", auth=admin_creds)
    assert response.status_code == status.HTTP_200_OK
    session_id = response.json()["session_id"]

    response = api_client.get("/employees", auth=admin_creds)
    assert response.status_code == status.HTTP_200_OK
    assert any(emp["emp_no"] == emp_no for emp in response.json())

    new_last_name = "Integration"
    response = api_client.put(
        f"/employees/{emp_no}/last-name",
        json={"last_name": new_last_name},
        auth=admin_creds,
        headers={"X-Session-Id": session_id},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["last_name"] == new_last_name

    response = api_client.get(
        f"/employees/{emp_no}",
        auth=admin_creds,
        headers={"X-Session-Id": session_id},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["last_name"] == new_last_name

    # Attempt to update with read-only credentials and expect a 403 error
    analyst_session = api_client.post("/sessions/start", auth=analyst_creds)
    assert analyst_session.status_code == status.HTTP_200_OK
    analyst_session_id = analyst_session.json()["session_id"]
    forbidden = api_client.put(
        f"/employees/{emp_no}/last-name",
        json={"last_name": "ShouldFail"},
        auth=analyst_creds,
        headers={"X-Session-Id": analyst_session_id},
    )
    assert forbidden.status_code == status.HTTP_403_FORBIDDEN

    # Revert the change so subsequent runs start from the golden state
    revert = api_client.put(
        f"/employees/{emp_no}/last-name",
        json={"last_name": original_last},
        auth=admin_creds,
        headers={"X-Session-Id": session_id},
    )
    assert revert.status_code == status.HTTP_200_OK
    assert revert.json()["last_name"] == original_last

    api_client.post("/sessions/end", auth=admin_creds, headers={"X-Session-Id": session_id})
    api_client.post(
        "/sessions/end",
        auth=analyst_creds,
        headers={"X-Session-Id": analyst_session_id},
    )
