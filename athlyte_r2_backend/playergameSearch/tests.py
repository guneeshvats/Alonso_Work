from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

# Create your tests here.

class SearchPlayerTests(APITestCase):
    def test_search_players(self):
        url = '/search/'
        data = {
            'UserId': 1,
            'SportCode': 'MFB',
            'BasicQuery': 'ReceptionYards > 50',
            'Entity': 'Player',
            'TimePeriod': 'Game',
            'FromOffset': 0,
            'ToOffset': 5
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)