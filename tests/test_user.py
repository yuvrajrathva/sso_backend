from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_read_users():
    response = client.get("/")
    assert response.status_code == 200


def test_signup_user_email():
    response = client.post("/signup", json={"roll_no":"19UCS001", "first_name":"Test", "last_name":"User", "email":"user@gmail.com", "password":"Test@123", "phone_number":"1234567890", "is_verified":False})
    assert response.status_code == 400
    assert response.json() == {'detail': 'Invalid email format'}


def test_signup_user_phone_number():
    response = client.post("/signup", json={"roll_no":"19UCS001", "first_name":"Test", "last_name":"User", "email":"user@iitj.ac.in", "password":"Test@123", "phone_number":"1234567890", "is_verified":False})
    assert response.status_code == 400
    assert response.json() == {'detail': 'Invalid phone number format'}


def test_signup_user_password():
    response = client.post("/signup", json={"roll_no":"19UCS001", "first_name":"Test", "last_name":"User", "email":"user@iitj.ac.in", "password":"helloworld", "phone_number":"9876543210", "is_verified":False})
    assert response.status_code == 400
    assert response.json() == {'detail': 'Password must contain at least one number'}
    