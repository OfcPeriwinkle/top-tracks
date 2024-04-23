# Top-Tracks
This is a simple CLI tool that scrapes the top singles for a given year from [Rate Your Music](https://rateyourmusic.com/) and create a Spotify playlist with them.

## Installation
First things first, clone this repository. Then create a virtual environment and install the submodule dependency and the package itself.

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

To get the top tracks of 1968, you can run:
```bash
top-tracks 2020 --pages 2
```
Here the `--pages` argument is optional and defaults to 1. It specifies the number of pages to scrape from Rate Your Music (~40 singles/page).
