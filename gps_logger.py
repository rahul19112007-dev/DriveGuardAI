import geocoder

def get_location():

    g = geocoder.ip("me")

    if g.latlng:

        return {
            "lat": g.latlng[0],
            "lng": g.latlng[1]
        }

    return None