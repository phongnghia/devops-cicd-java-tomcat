import os
import requests


EC2_PUBLIC_IP="13.250.24.85"


def test_api():
    url = "http://%s:8080/java_tomcat_application/api/hello" % EC2_PUBLIC_IP
    response = requests.get(url)
    assert response.status_code == 200, f"API Test Failed: {response.status_code}"
    print("API Test Passed!")

if __name__ == "__main__":
    test_api()
