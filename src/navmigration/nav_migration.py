import argparse
import requests
import hashlib
import random
import string
import urllib.parse as urlparse
from urllib.parse import urlencode

# Define server URL
source_server_url = "http://localhost:4533"
target_server_url = "http://localhost:4535"
api_version = "1.16.1"  # Set the API version


def add_url_params(url: str, params: list[tuple[str, str]]) -> str:
    """
    Use a list of tuples for key pairs to support multiple keys that have different values.
    """
    url_parts = list(urlparse.urlparse(url))
    query = urlparse.parse_qsl(url_parts[4])
    query.extend(params)
    url_parts[4] = urlencode(query)
    return urlparse.urlunparse(url_parts)


def _calculate_token(password: str) -> tuple:
    """
    Generate random salt of 6 chars and calculate token.
    :return: tuple(token, salt)
    """
    letters = string.ascii_lowercase
    salt = ''.join(random.choice(letters) for _ in range(6))
    token = hashlib.md5(f"{password}{salt}".encode("utf-8")).hexdigest()
    return token, salt


def _subsonic_format_url(username: str, password: str, url: str, params: list[tuple[str, str]] = None) -> str:
    """
    Format the URL with authentication parameters.
    """
    token, salt = _calculate_token(password)
    required_params = [
        ("u", username),
        ("t", token),
        ("s", salt),
        ("v", api_version),
        ("c", "myapp"),
        ("f", "json")
    ]
    if params:
        required_params.extend(params)

    url = add_url_params(url, required_params)
    return url


def get_playlists(server_url, username, password):
    url = _subsonic_format_url(username, password, f"{server_url}/rest/getPlaylists")
    response = requests.get(url)
    response.raise_for_status()
    d = response.json()
    return response.json()["subsonic-response"]['playlists']['playlist']


def get_playlist_details(server_url, username, password, playlist_id):
    url = _subsonic_format_url(username, password, f"{server_url}/rest/getPlaylist", [("id", playlist_id)])
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["subsonic-response"]['playlist']


def get_song(server_url, username, password, song_id):
    url = _subsonic_format_url(username, password, f"{server_url}/rest/getSong", [("id", song_id)])
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["subsonic-response"]['song']


def create_playlist(server_url, username, password, name):
    url = _subsonic_format_url(username, password, f"{server_url}/rest/createPlaylist", [("name", name)])
    response = requests.post(url)
    response.raise_for_status()
    return response.json()["subsonic-response"]['playlist']['id']


def add_track_to_playlist(server_url, username, password, playlist_id, track_id):
    url = _subsonic_format_url(username, password, f"{server_url}/rest/updatePlaylist",
                               [("playlistId", playlist_id), ("songIdToAdd", track_id)])
    response = requests.post(url)
    response.raise_for_status()


def set_track_rating(server_url, username, password, track_id, rating):
    url = _subsonic_format_url(username, password, f"{server_url}/rest/setRating",
                               [("id", track_id), ("rating", rating)])
    response = requests.post(url)
    response.raise_for_status()


def main(source_username, source_password, target_username, target_password):
    # Get playlists from the source server
    source_playlists = get_playlists(source_server_url, source_username, source_password)

    for source_playlist in source_playlists:
        source_playlist_details = get_playlist_details(source_server_url, source_username, source_password,
                                                       source_playlist['id'])

        # Create playlists on the target server
        target_playlist_id = create_playlist(target_server_url, target_username, target_password, source_playlist['name'])

        # Process each track in the source playlist
        entries = source_playlist_details.get('entry')
        if not entries:
            continue
        for entry in entries:
            # the entry of the playlist does not always have the 'userRating' field present. Workaround this by calling 'getSong' api.
            song_entry = get_song(source_server_url, source_username, source_password, entry['id'])
            track_id = song_entry['id']
            track_rating = song_entry.get('userRating', 0)

            target_track_id = track_id
            target_song_entry = get_song(target_server_url, target_username, target_password, entry['id'])
            assert target_song_entry['title'] == song_entry['title']

            # Add track to the target playlist
            add_track_to_playlist(target_server_url, target_username, target_password, target_playlist_id, target_track_id)

            # Set the rating of the track on the target server
            if track_rating:
                set_track_rating(target_server_url, target_username, target_password, target_track_id, track_rating)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('source_username')
    argument_parser.add_argument('source_password')
    argument_parser.add_argument('target_username')
    argument_parser.add_argument('target_password')
    args = argument_parser.parse_args()
    main(args.source_username, args.source_password, args.target_username, args.target_password)
