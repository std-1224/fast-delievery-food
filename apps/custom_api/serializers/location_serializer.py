from rest_framework import serializers

class LocationSerializer(serializers.Serializer):
    address = serializers.CharField()
    # Add other fields if your location data has them, e.g., postcode, city, etc.
    # postcode = serializers.CharField()
    # city = serializers.CharField() 