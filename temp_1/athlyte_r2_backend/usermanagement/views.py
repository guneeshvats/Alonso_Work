from decouple import config
import bcrypt
from .serializers import *
from .models import *
from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from pymongo import MongoClient
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import re
import logging


# Get MongoDB connection string from environment variables
mongo_uri = config('DB_URI')
db_name = config('DB_NAME')

# Connect to MongoDB using PyMongo
client = MongoClient(mongo_uri)
db = client[db_name]
user_collection = db['users']

logging.basicConfig(
    level=logging.INFO,  # You can set this to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger()


@swagger_auto_schema(
    method='post',
    request_body=AuthenticateInputSerializer,
    responses={200: AuthOutputSerializer(many=True)},
)
@api_view(['POST'])
def authenticate_user(request):
    # Validate input using the serializer
    # Using serializers for now as we have mock data stored in Python script
    serializer = AuthenticateInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    validated_data = serializer.validated_data
    username = validated_data.get('UserName')
    password = validated_data.get('Password')
    try:
        user_valid, user_data = is_user_valid(username, password)
        if not user_valid:
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
        refresh = generate_refresh_token(user_data)
        access_token = str(refresh)
        auth_response = {
            'email': user_data['email'],
            'username': user_data['username'],
            'team': user_data['team'],
            'sports': user_data['sports'],
            'accesstoken': access_token
        }
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(auth_response, status=status.HTTP_200_OK)


def generate_refresh_token(user_data):
    # Extract necessary user data
    user_id = str(user_data.get('_id'))
    username = user_data.get('username')
    email = user_data.get('email')
    # Instantiate the custom user object
    custom_user = User(user_id=user_id, username=username, email=email)
    # Generate refresh token for the custom user object
    refresh_token = RefreshToken.for_user(custom_user)
    return refresh_token


def is_user_valid(username, password):
    user_res = user_collection.find_one({'username': username, 'isActive': True})
    if user_res is None:
        return False, None
    encoded_password = password.encode('utf-8')
    db_hashed_pwd = user_res['hashedPwd']
    is_pwd_valid = bcrypt.checkpw(encoded_password, db_hashed_pwd.encode('utf-8'))
    if not is_pwd_valid:
        return False, None
    return True, user_res


@swagger_auto_schema(
    method='post',
    request_body=UserInputSerializer,
    responses={200: CreateUserOutputSerializer(many=True)},
)
@api_view(['POST'])
def create_user(request):
    serializer = UserInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    validated_data = serializer.validated_data
    username = validated_data.get('UserName')
    password = validated_data.get('Password')
    user_res = user_collection.find_one({'$and': [{'userName': username}, {'isActive': True}]})

    if user_res is not None:
        return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Hash the password using bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        # Create a new user with hashed password
        user_data = {
            "email": validated_data.get('Email'),
            "team": validated_data.get('Team'),
            "sports": validated_data.get('Sports'),
            "username": username,
            "isActive": True,
            "hashedPwd": hashed_password.decode('utf-8')
        }
        user_id = str(user_collection.insert_one(user_data).inserted_id)

        return Response({
            "userid": user_id,
            "username": username
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
