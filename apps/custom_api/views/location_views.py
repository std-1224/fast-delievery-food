from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.custom_api.serializers.location_serializer import LocationSerializer

# Import geocoding libraries
from django.http import JsonResponse # Although not used directly by APIView, good to have if needed
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# Replace the mock implementation with actual search logic using Nominatim
def search_locations_by_postcode(postcode_query):
    suggestions = []
    geolocator = Nominatim(user_agent="oscar-checkout-app") # Use an appropriate user agent

    if postcode_query:
        try:
            # Use the provided query directly with geocode
            locations = geolocator.geocode(postcode_query, exactly_one=False, limit=10) # Increased limit slightly
            if locations:
                for location in locations:
                    # The provided logic extracts components, but for the current serializer
                    # which only expects 'address', we can directly use the full address.
                    # If you need more detailed fields, update LocationSerializer.
                    suggestion_data = {
                         'address': location.address, # Map full address to 'address' for the serializer
                         # You could add other fields here if LocationSerializer is updated:
                         # 'line1': address_components.get('road', ''),
                         # 'line4': address_components.get('city', address_components.get('town', address_components.get('village', ''))),
                         # 'postcode': address_components.get('postcode', ''),
                         # 'country': address_components.get('country', ''),
                    }
                    suggestions.append(suggestion_data)
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            print(f"Geocoding error: {e}")
            # Optionally return an empty list or an error indicator
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            # Optionally return an empty list or an error indicator
            return []

    return suggestions

class PostcodeAutocompleteView(APIView):
    """ API view for postcode autocomplete. """

    def get(self, request, *args, **kwargs):
        postcode_query = request.query_params.get('postcode', None)

        if not postcode_query:
            return Response({"error": "Postcode parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Get locations using the new geocoding logic
        locations = search_locations_by_postcode(postcode_query)

        # Serialize the data using the existing serializer
        # The serializer expects a list of objects with an 'address' key
        serializer = LocationSerializer(locations, many=True)

        return Response(serializer.data) 