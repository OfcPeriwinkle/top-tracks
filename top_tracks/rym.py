import argparse
import logging

from typing import Dict, List, Tuple

import dotenv
import jaro
import spotipy
import tqdm

from rymscraper import rymscraper, RymUrl
from spotipy.oauth2 import SpotifyOAuth

logging.basicConfig(level=logging.INFO)


def get_args():
    """
    Get the command line arguments.
    """

    parser = argparse.ArgumentParser(
        description='Create a Spotify playlist based on the top tracks of a given year (or all time)')
    parser.add_argument('--years', type=str, default='all-time',
                        help='The year to get the top tracks from')
    parser.add_argument('--pages', type=int, default=1, help='The number of pages to scrape')
    parser.add_argument(
        '--genres',
        nargs='+',
        default=None,
        help='The genres to filter the top tracks by; separate multiple genres with spaces; '
        'if a genre has a space use a hyphen (e.g. New Wave -> new-wave)')
    parser.add_argument(
        '--kind',
        default='single',
        choices=['single', 'album'],
        help='The type of release to filter the top tracks by; defaults to single')
    return parser.parse_args()


def get_chart_entries(
        years: str = 'all-time',
        genres: List[str] = None,
        kind: str = 'single',
        pages: int = 1) -> List[Dict]:
    """
    Get the top tracks from Rate Your Music, filtering for provided year(s), genre(s), and kind.

    Args:
        years: The year to get the top tracks from; defaults to 'all-time'
        genres: The genres to filter the top tracks by; defaults to None
        kind: The type of release to filter the top tracks by; defaults to 'single'
        pages: The number of pages to scrape; defaults to 1

    Returns:
        A list of dictionaries containing the top tracks
    """

    url = RymUrl.RymUrl(year=years, kind=kind, language='en',
                        genres=','.join(genres) if genres else None)
    network = rymscraper.RymNetwork()

    try:
        logging.info(f'Getting top tracks from {url}')
        list_rows = network.get_chart_infos(url, max_page=pages)
    except Exception as e:
        logging.error(f'Error getting top tracks: {e}')
    finally:
        network.browser.quit()

    return list_rows


def unique_tracks(tracks: List[str]) -> List[str]:
    """
    Remove duplicates from a list of tracks while preserving the order.

    Taken from https://stackoverflow.com/questions/480214/how-do-i-remove-duplicates-from-a-list-while-preserving-order

    Args:
        tracks: A list of track URIs

    Returns:
        A list of unique track URIs with their order preserved
    """

    seen = set()
    return [track for track in tracks if not (track in seen or seen.add(track))]


def search_for_single_uris(sp: spotipy.Spotify, tracks: List[Dict]) -> List[str]:
    """
    Search for a list of tracks on Spotify and return the unique URIs.

    Args:
        sp: The Spotify object
        tracks: A list of track dictionaries

    Returns:
        A list of unique track URIs
    """

    spotify_uris = []

    for track in tqdm.tqdm(tracks, desc='Searching for top tracks on Spotify'):
        songs = track['Album'].split(' / ')

        for song in songs:
            # Search for the track on Spotify using fuzzy matching; using the artist and track
            # filters may cause unexpected results to leak through if RYM and Spotify don't match
            res = sp.search(q=f'{song} by {track["Artist"]}', type='track')

            for item in res['tracks']['items']:
                # Names can be inconsistent between RYM and Spotify; use
                # Jaro-Winkler similarity to see if we have something close enough
                artist_similarity = jaro.jaro_winkler_metric(
                    item["artists"][0]["name"], track["Artist"])
                track_similarity = jaro.jaro_winkler_metric(item["name"], song)

                if artist_similarity > 0.7 and track_similarity > 0.7:
                    spotify_uris.append(item['uri'])
                    break

    return unique_tracks(spotify_uris)


def create_playlist_name_and_description(year: str, genres: List[str] = None) -> Tuple[str, str]:
    """
    Create the name and description for the Spotify playlist.

    Args:
        year: The year to get the top tracks from
        genres: The genres to filter the top tracks by; defaults to None

    Returns:
        A tuple containing the playlist name and description
    """

    display_genres = [genre.replace("-", " ").title()
                      for genre in genres] if genres else []
    genre_description = f'{", ".join(display_genres)}' if genres else ''
    display_year = year if year != 'all-time' else 'All Time'

    # Add 'the' to the beginning of decades
    if display_year[-1] == 's':
        display_year = f'the {display_year}'

    display_preposition = 'from' if display_year != 'All Time' else 'of'

    playlist_name = [
        'RYM Top',
        f'{", ".join(display_genres) if display_genres else "Tracks"}',
        display_preposition,
        display_year
    ]
    playlist_description = [
        'The top',
        genre_description.lower(),
        'tracks',
        display_preposition,
        display_year.lower(),
        'according to Rate Your Music.',
        'Generated by https://github.com/OfcPeriwinkle/top-tracks.'
    ]

    return ' '.join(playlist_name), ' '.join(playlist_description)


def get_album_tracks(
        sp: spotipy.Spotify,
        chart_entries: List[Dict],
        size_limit: int = 3) -> List[str]:
    """
    Get the top size_limit most popular tracks from the top albums on Spotify.

    Args:
        sp: The Spotify object
        chart_entries: A list of album dictionaries
        size_limit: The number of tracks to get from each album; defaults to 3

    Returns:
        A list of unique track URIs
    """

    track_uris = []

    for entry in tqdm.tqdm(
            chart_entries,
            desc='Collecting most popular tracks from top albums on Spotify'):
        res = sp.search(q=f'{entry["Album"]} by {entry["Artist"]}', type='album')
        album = None

        for item in res['albums']['items']:
            artist_similarity = jaro.jaro_winkler_metric(
                item['artists'][0]['name'], entry['Artist'])
            album_similarity = jaro.jaro_winkler_metric(item['name'], entry['Album'])

            if artist_similarity > 0.7 and album_similarity > 0.7:
                album = item['uri']
                break

        if album is None:
            continue

        tracks = sp.album_tracks(album)
        track_details = sp.tracks([track['uri'] for track in tracks['items']])['tracks']
        track_details.sort(key=lambda x: x['popularity'], reverse=True)

        track_uris.extend([details['uri'] for details in track_details]
                          [:size_limit if len(track_details) >= size_limit else len(track_details)])

    return unique_tracks(track_uris)


def create_spotify_playlist(
        sp: spotipy.Spotify,
        spotify_uris: set,
        playlist_name: str,
        playlist_description: str) -> str:
    """
    Create a Spotify playlist with the given URIs.

    Args:
        sp: The Spotify object
        spotify_uris: A set of track URIs
        playlist_name: The name of the playlist
        playlist_description: The description of the playlist

    Returns:
        The URL of the created playlist
    """

    user = sp.current_user()
    res = sp.user_playlist_create(
        user=user['id'],
        name=playlist_name,
        public=False,
        description=playlist_description)

    spotify_uris = list(spotify_uris)
    chunked_uris = [spotify_uris[i:i + 100] for i in range(0, len(spotify_uris), 100)]

    for chunk in tqdm.tqdm(chunked_uris, desc='Adding track chunks to playlist'):
        sp.user_playlist_add_tracks(
            user=user['id'],
            playlist_id=res['id'],
            tracks=chunk)

    return res['external_urls']['spotify']


def main():
    """
    Parse command line args and create a Spotify playlist based on the top tracks from RYM.
    """

    args = get_args()
    scope = "user-library-read,playlist-modify-private"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    logging.info(f'Getting top tracks for {args.years} from RYM...')
    chart_entries = get_chart_entries(args.years, args.genres, args.kind, args.pages)

    if not chart_entries:
        logging.error('No tracks found')
        return

    if args.kind == 'album':
        spotify_uris = get_album_tracks(sp, chart_entries)
    else:
        spotify_uris = search_for_single_uris(sp, chart_entries)

    playlist_name, playlist_description = create_playlist_name_and_description(
        args.years, args.genres)
    url = create_spotify_playlist(sp, spotify_uris, playlist_name, playlist_description)

    logging.info(f'Playlist created: {url}')


if __name__ == '__main__':
    dotenv.load_dotenv()
    main()
