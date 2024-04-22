import dotenv
import spotipy

from typing import List, Dict
from rymscraper import rymscraper, RymUrl
from spotipy.oauth2 import SpotifyOAuth

YEAR = 1968


def get_top_tracks(year: int, pages: int = 1) -> List[Dict]:
    url = RymUrl.RymUrl(year=year, kind="single", language='en')
    RymNetwork = rymscraper.RymNetwork()
    list_rows = RymNetwork.get_chart_infos(url, max_page=pages)

    return list_rows


def main():
    scope = "user-library-read,playlist-modify-private"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    top_tracks = get_top_tracks(YEAR)
    spotify_uris = []

    for track in top_tracks:
        songs = track['Album'].split(' / ')

        for song in songs:
            res = sp.search(q=f'artist:{track["Artist"]} track:{song}', type='track')

            try:
                spotify_uris.append(res['tracks']['items'][0]['uri'])
            except IndexError:
                pass

    user = sp.current_user()
    res = sp.user_playlist_create(
        user=user['id'],
        name=f'Top Tracks of {YEAR}',
        public=False,
        description=f'The top singles of {YEAR} according to Rate Your Music')

    sp.user_playlist_add_tracks(
        user=user['id'],
        playlist_id=res['id'],
        tracks=spotify_uris)


if __name__ == '__main__':
    dotenv.load_dotenv()
    main()
