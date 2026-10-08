from bson import ObjectId
from rest_framework import serializers

class AuthenticateInputSerializer(serializers.Serializer):
    UserName = serializers.CharField(required=True)
    Password = serializers.CharField(required=True)

class UserInputSerializer(serializers.Serializer):
    UserName = serializers.CharField(required=True)
    Password = serializers.CharField(required=True)
    Team = serializers.DictField(child=serializers.JSONField(), required=False)
    Sports = serializers.ListField(
        child=serializers.DictField(child=serializers.JSONField()),
        required=False
    )
    Email = serializers.CharField(required=True)



class AuthOutputSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    email =  serializers.CharField(required=True)
    team = serializers.DictField(child=serializers.JSONField(), required=False)
    sports = serializers.DictField(child=serializers.JSONField(), required=False)
    accesstoken = serializers.CharField(required=True)



class CreateUserOutputSerializer(serializers.Serializer):
    userid = serializers.CharField(required=True)
    username = serializers.CharField(required=True)