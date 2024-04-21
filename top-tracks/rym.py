import dotenv
import spotipy

from rymscraper import rymscraper, RymUrl
from spotipy.oauth2 import SpotifyClientCredentials

dotenv.load_dotenv()


def main():
    spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

    url = RymUrl.RymUrl(year=1968, kind="single", language='en')
    RymNetwork = rymscraper.RymNetwork()
    list_rows = RymNetwork.get_chart_infos(url, max_page=1)

    for row in list_rows:
        songs = row['Album'].split(' / ')
        print(row['Artist'], songs, row['Genres'], row['Date'])

        for song in songs:
            res = spotify.search(q=f'artist:{row["Artist"]} track:{song}', type='track')

            try:
                print('\t', res['tracks']['items'][0]['name'], res['tracks']
                      ['items'][0]['external_urls']['spotify'])
            except IndexError:
                print('\t', 'No results found')


if __name__ == '__main__':
    main()
