from typing import List

import spotipy
from flask import Flask, request

import rym

app = Flask(__name__)


def parse_kinds(kinds: str) -> str:
    kinds = kinds.split(',')

    if len(kinds) > 1:
        raise NotImplementedError('Multiple kinds are not supported')

    if kinds[0] not in ('album', 'track'):
        raise NotImplementedError(f'Kind: {kinds[0]} is not supported')

    return kinds[0]


def parse_genres(genres: str) -> List[str]:
    if genres[:2] == 'g:':
        genres = genres[2:]

    return genres.split(',')


@app.route('/rym/charts/top/<kinds>/<years>/<genres>/<int:pages>', methods=['GET'])
def rym_chart(kinds: str, years: str, genres: str, pages: int):
    kinds = parse_kinds(kinds)
    genres = parse_genres(genres)

    body = request.get_json()
    access_token = body['auth']
    sp = spotipy.Spotify(access_token)

    chart_entries = rym.get_chart_entries(years, genres, kinds, pages)

    if not chart_entries:
        return {'message': 'No tracks found'}, 404

    if kinds == 'album':
        spotify_uris = rym.get_album_tracks(sp, chart_entries)
    else:
        spotify_uris = rym.search_for_single_uris(sp, chart_entries)

    playlist_name, playlist_description = rym.create_playlist_name_and_description(years, genres)
    url = rym.create_spotify_playlist(sp, spotify_uris, playlist_name, playlist_description)

    return {'playlist': url}


if __name__ == '__main__':
    app.run()
