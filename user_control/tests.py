from rest_framework.test import APITestCase
from .views import get_random, get_access_token, get_refresh_token
from .models import CustomUser, UserProfile
from message_control.tests import create_image, SimpleUploadedFile


class TestGenericFunctions(APITestCase):

    def test_get_random(self):

        rand1 = get_random(10)
        rand2 = get_random(10)
        rand3 = get_random(15)

        # check that we are getting a result
        self.assertTrue(rand1)

        # check that rand1 is not equal to rand2
        self.assertNotEqual(rand1, rand2)

        # check that the length of result is what is expected
        self.assertEqual(len(rand1), 10)
        self.assertEqual(len(rand3), 15)

    def test_get_access_token(self):
        payload = {
            "id": 1
        }

        token = get_access_token(payload)

        # check that we obtained a result
        self.assertTrue(token)

    def test_get_refresh_token(self):

        token = get_refresh_token()

        # check that we obtained a result
        self.assertTrue(token)


class TestAuth(APITestCase):
    login_url = "/user/login"
    register_url = "/user/register"
    refresh_url = "/user/refresh"

    def test_register(self):
        payload = {
            "username": "testuser1",
            "password": "password1234",
            "email": "testemail@google.com"
        }

        response = self.client.post(self.register_url, data=payload)

        # check that we obtain a status of 201
        self.assertEqual(response.status_code, 201)

    def test_login(self):
        payload = {
            "username": "testuser1",
            "password": "password1234",
            "email": "testemail@google.com"
        }

        # register
        self.client.post(self.register_url, data=payload)

        # login
        response = self.client.post(self.login_url, data=payload)
        result = response.json()

        # check that we obtain a status of 200
        self.assertEqual(response.status_code, 200)

        # check that we obtained both the refresh and access token
        self.assertTrue(result["access"])
        self.assertTrue(result["refresh"])

    def test_refresh(self):
        payload = {
            "username": "testuser1",
            "password": "password1234",
            "email": "testemail@google.com"
        }

        # register
        self.client.post(self.register_url, data=payload)

        # login
        response = self.client.post(self.login_url, data=payload)
        refresh = response.json()["refresh"]

        # get refresh
        response = self.client.post(self.refresh_url, data={"refresh":refresh})
        result = response.json()

        # check that we obtain a status of 200
        self.assertEqual(response.status_code, 200)
        # check that we obtained both the refresh and access token
        self.assertTrue(result["access"])
        self.assertTrue(result["refresh"])


class TestUserInfo(APITestCase):
    profile_url = "/user/profile"
    file_upload_url = "/message/file-upload"
    login_url = "/user/login"

    def setUp(self):
        payload = {
            "username": "test_user2",
            "password": "password1234",
            "email": "testemail3@google.co.kr"
        }
        self.user = CustomUser.objects._create_user(**payload)
        
        # login
        response = self.client.post(self.login_url, data=payload)
        result = response.json()

        self.bearer = {
            'HTTP_AUTHORIZATION': 'Bearer {}'.format(result['access'])}

    def test_post_user_profile(self):
        payload = {
            "user_id" : self.user.id,
            "first_name": "Test",
            "last_name": "User2",
            "caption": "Being alive is different from living",
            "about": "I am a passionation lover of ART, graphics and creation"
        }

        response = self.client.post(self.profile_url, data=payload, **self.bearer)
        result = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(result["first_name"], "Test")
        self.assertEqual(result["last_name"], "User2")
        self.assertEqual(result["user"]["username"], "test_user2")
        

    def test_post_user_profile_with_profile_picture(self):

        # upload image
        avatar = create_image(None, "avatar.png")
        avatar_file = SimpleUploadedFile("front1.png", avatar.getvalue())
        data = {
            "file_upload": avatar_file
        }

        # processing
        response = self.client.post(self.file_upload_url, data=data, **self.bearer)
        result = response.json()

        payload = {
            "user_id" : self.user.id,
            "first_name": "Test",
            "last_name": "User2",
            "caption": "Being alive is different from living",
            "about": "I am a passionation lover of ART, graphics and creation",
            "profile_picture_id": result["id"]
        }

        response = self.client.post(self.profile_url, data=payload, **self.bearer)
        result = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(result["first_name"], "Test")
        self.assertEqual(result["last_name"], "User2")
        self.assertEqual(result["user"]["username"], "test_user2")
        self.assertEqual(result["profile_picture"]["id"], 1)
        
    def test_update_user_profile(self):
        # create profile

        payload = {
            "user_id" : self.user.id,
            "first_name": "Test",
            "last_name": "User2",
            "caption": "Being alive is different from living",
            "about": "I am a passionation lover of ART, graphics and creation"
        }

        response = self.client.post(self.profile_url, data=payload, **self.bearer)
        result = response.json()

        # --- created profile

        payload = {
            "first_name": "TEST",
            "last_name": "USER3",
        }

        response = self.client.patch(self.profile_url + f"/{result['id']}", data=payload, **self.bearer)
        result = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(result["first_name"], "TEST")
        self.assertEqual(result["last_name"], "USER3")
        self.assertEqual(result["user"]["username"], "test_user2")

    def test_user_search(self):

        UserProfile.objects.create(user=self.user, first_name="Adefemi", last_name="oseni",
                                    caption="it's all about testing", about="I'm a developer")

        user2 = CustomUser.objects._create_user(
            username="tester", password="tester1234", email="testemail4@google.co.kr")
        UserProfile.objects.create(user=user2, first_name="Vester", last_name="Mango",
                                    caption="it's all about testing", about="I'm a developer")

        user3 = CustomUser.objects._create_user(
            username="vasman", password="vasman123", email="testemail5@google.co.kr")
        UserProfile.objects.create(user=user3, first_name="Adeyemi", last_name="Boseman",
                                   caption="it's all about testing", about="I'm a youtuber")

        
        url = self.profile_url + "?keyword=adefemi oseni"

        response = self.client.get(url, **self.bearer)
        result = response.json()["results"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(result), 0)

        url = self.profile_url + "?keyword=ade"

        response = self.client.get(url, **self.bearer)
        result = response.json()["results"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["user"]["username"], "vasman")

        # test keyword = ade
        url = self.profile_url + "?keyword=ade"

        response = self.client.get(url, **self.bearer)
        result = response.json()["results"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["user"]["username"], "vasman")

        # test keyword = vester
        url = self.profile_url + "?keyword=vester"

        response = self.client.get(url, **self.bearer)
        result = response.json()["results"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["user"]["username"], "tester")