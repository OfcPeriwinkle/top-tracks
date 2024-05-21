# Top-Tracks
This is a simple CLI tool that scrapes the top singles or albums within an optional timeframe from [Rate Your Music](https://rateyourmusic.com/) and creates a Spotify playlist with them.

## Installation
First thing's first, clone this repository. Then create a virtual environment and install the submodule dependency and the package itself.

In a nutshell:
```bash
git clone git@github.com:OfcPeriwinkle/top-tracks.git
cd top-tracks
python3 -m venv .venv
source .venv/bin/activate
git submodule update --init --recursive
pip install submodules/rymscraper/. .
```

## Environment Variables
You will need to set the following environment variables:
- `SPOTIPY_CLIENT_ID`: Your Spotify client ID.
- `SPOTIPY_CLIENT_SECRET`: Your Spotify client secret.
- `SPOTIPY_REDIRECT_URI`: Your Spotify redirect URI.

More information on these variables can be found in the [Spotipy documentation](https://spotipy.readthedocs.io/).

## Usage
Since this is just a CLI tool right now, you can run `top-tracks -h` to see the full list of arguments.

To get the top tracks of 2020, you can run:
```bash
top-tracks --years 2020 --pages 2
```
Here the `--pages` argument is optional and defaults to 1. It specifies the number of pages to scrape from Rate Your Music (~40 singles/page).

Some advanced playlists can be made by using date ranges, genre filters, and switching between album/single modes:
```bash
top-tracks --years 2006-2024 --genres indie pop --kind album
```

This command will create a playlist of the most popular tracks from the top indie pop albums that were released between 2006 and 2024.
