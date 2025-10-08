import pytest
from fastapi.testclient import TestClient
from main import app
from models import TPReview


@pytest.fixture
def client(db_session):
    """
    Create a TestClient while db_session (from conftest) has already overridden main.SessionLocal.
    Seed test data into db_session, commit, then yield a TestClient that will use the same sessionmaker.
    """
    # seed test data (unique Review_Id values)
    db_session.add_all([
        TPReview(Review_Id=1, Reviewer_Id=456, Reviewer_Name="Test User",
                 Review_Title="Great!", Review_Rating=5, Business_Id="biz1"),
        TPReview(Review_Id=2, Reviewer_Id=789, Reviewer_Name="Another User",
                 Review_Title="Good", Review_Rating=4, Business_Id="biz2"),
    ])
    db_session.commit()

    with TestClient(app) as c:
        yield c


def test_get_reviews_for_business(client):
    # note:  seed Business_Id 'biz1' above, so request that business
    response = client.get("/business/biz1/reviews")
    assert response.status_code == 200

    # streaming CSV includes header; ensure header present and seeded row exists
    assert response.text.startswith("Review_Id,Reviewer_Name,Review_Title,Review_Rating")
    assert "Great!" in response.text
    assert "biz1" in response.text


def test_get_reviews_by_user(client):
    response = client.get("/user/789/reviews")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Another User" in response.text
    # ensure the row for Review_Id=2 is present in CSV
    assert "2,Another User,Good,4" in response.text


def test_get_user_account(client):
    response = client.get("/user/456/account")
    assert response.status_code == 200
    data = response.json()
    assert str(data["Reviewer_Id"]) == "456"
    assert data["Reviewer_Name"] == "Test User"
