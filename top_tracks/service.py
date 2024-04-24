import os
from typing import List

import dotenv
import spotipy
from flask import Flask, session, request, redirect, render_template
from flask_session import Session

import rym

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)


def parse_kinds(kinds: str) -> str:
    kinds = kinds.split(',')

    if len(kinds) > 1:
        raise NotImplementedError('Multiple kinds are not supported')

    if kinds[0] not in ('album', 'single'):
        raise NotImplementedError(f'Kind: {kinds[0]} is not supported')

    return kinds[0]


def parse_genres(genres: str) -> List[str]:
    if len(genres) == 0:
        return []

    if genres[:2] == 'g:':
        genres = genres[2:]

    raw_genres = genres.split(',')

    return [genre.strip() for genre in raw_genres]


def verify_credentials():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return None

    return auth_manager


@app.route('/')
def index():

    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        scope='user-read-currently-playing playlist-modify-private',
        cache_handler=cache_handler,
        show_dialog=True)

    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return render_template('base.html', auth_url=auth_url)

    # Step 3. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return render_template('index.html', spotify=spotify)


@app.route('/sign_out')
def sign_out():
    session.pop("token_info", None)
    return redirect('/')


@app.route('/rym/charts/top', methods=['POST'])
def rym_chart():
    kinds = parse_kinds(request.form.get('kinds', 'single'))
    genres = parse_genres(request.form.get('genres', ''))
    years = request.form.get('years', 'all-time')
    pages = int(request.form.get('pages', 1))

    auth_manager = verify_credentials()

    if not auth_manager:
        return redirect('/')

    sp = spotipy.Spotify(auth_manager=auth_manager)

    chart_entries = rym.get_chart_entries(years, genres, kinds, pages)

    if not chart_entries:
        return {'message': 'No tracks found'}, 404

    if kinds == 'album':
        spotify_uris = rym.get_album_tracks(sp, chart_entries)
    else:
        spotify_uris = rym.search_for_single_uris(sp, chart_entries)

    playlist_name, playlist_description = rym.create_playlist_name_and_description(years, genres)
    url = rym.create_spotify_playlist(sp, spotify_uris, playlist_name, playlist_description)

    return redirect(url)


if __name__ == '__main__':
    dotenv.load_dotenv()
    app.run(port=8888, threaded=True)
