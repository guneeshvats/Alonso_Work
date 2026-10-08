from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

# Create your tests here.

class UserManagementTests(APITestCase):
    def test_user_login(self):
        url = '/user/login/'
        data = {
            'UserName': 'rekha.g',
            'Password': 'test@123'}
        response = self.client.post(url, data, format='json')
        print(response.status_code)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_user(self):
        url = '/user/create/'
        data = {
            'UserName': 'rekha.g',
            'Password': 'test@123',
            'Team': {
                'code': 31,
                'name': 'Arkansas',
                'gTeamId': 33,
                'tidyName': 'ARK',
                'imgUrl': 'http://se-img.dcd-production.i.geniussports.com/ce4db9aa510ee71605ac7713c6b57dbfT1.png',
                'colorCode': '#a12338'
            },
            'Sports': [
                {'name': 'Football', 'code': 'MFB', 'gLeagueId': 4},
                {'name': 'Basketball(M)', 'code': 'MBB', 'gLeagueId': 456}
            ],
            'Email': 'rekha.g@example.com'
        }

        response = self.client.post(url, data, format='json')
        print(response.status_code)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


