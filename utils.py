import os
import google.generativeai as genai
import requests

def get_gemini_response(symptoms, urgency, location=None):
    prompt = f"""
    Analyze the following patient symptoms and provide structured output:
    - Emergency level (Emergency / Urgent / Normal)
    - Should the patient call an ambulance? (Yes/No + reason)
    - Possible condition (general, not medical diagnosis)
    - Immediate first aid suggestions
    - Safety advice

    Symptoms: {symptoms}
    Urgency: {urgency}
    Location: {location if location else 'Not provided'}
    """
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3-flash-preview")
    response = model.generate_content(prompt)
    return response.text

def get_coordinates(address):
    """Convert address to latitude/longitude using Google Geocoding API."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
    return None, None

def find_nearby_hospitals(lat, lng, radius=10000):
    """Find nearby hospitals using Google Places API."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=hospital&key={api_key}"
    response = requests.get(url)
    hospitals = []
    if response.status_code == 200:
        data = response.json()
        for place in data.get('results', [])[:3]:  # Top 3
            hospital = {
                'name': place.get('name'),
                'address': place.get('vicinity'),
                'rating': place.get('rating', 'N/A'),
                'place_id': place.get('place_id'),
                'lat': place['geometry']['location']['lat'],
                'lng': place['geometry']['location']['lng']
            }
            hospitals.append(hospital)
    return hospitals

def get_hospital_details(place_id):
    """Get hospital details including phone number."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_phone_number&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        result = data.get('result', {})
        return result.get('formatted_phone_number', 'Contact not available')
    return 'Contact not available'

def get_directions(origin_lat, origin_lng, dest_lat, dest_lng):
    """Get directions from user to hospital."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    origin = f"{origin_lat},{origin_lng}"
    destination = f"{dest_lat},{dest_lng}"
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['routes']:
            route = data['routes'][0]['legs'][0]
            distance = route['distance']['text']
            duration = route['duration']['text']
            return distance, duration
    return 'N/A', 'N/A'

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate approximate distance in km (Haversine formula)."""
    import math
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 1)
