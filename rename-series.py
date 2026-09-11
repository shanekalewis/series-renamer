"""
Rename-Series

Tool to facillitate renaming episodes in series (ARM -> Jellyfin)
"""
from argparse import ArgumentParser
from glob import glob
import json
import os
import shutil

def print_example_json():
    example_config = [
        {
            "series_name": "Test Series",
            "season": 1,
            "epsisode_start": 5,
            "episode_titles": ["Title 1", "Title 2"],
            "extra_titles": [
                "<title-for-extras>"
            ],
            "source_videos": "<path-to-source-videos>",
            "output": "<path-to-video-library>" 
        }
    ]

    with open("example.json", "w", encoding="utf-8") as fp:
        json.dump(example_config, fp, indent=4)

def validate_filename_characters(filename):
    updated_filename = filename

    forbidden_chars = {
        "/": "╱"
    }

    for c in forbidden_chars:
        if c in updated_filename:
            updated_filename = updated_filename.replace(c, forbidden_chars[c])

    return updated_filename

class SeriesSection:
    videos: dict        # Dictionary of source videos mapped to destination video
    series_name: str    # Name of the series - will be the directory create under the output directory
    season: int         # Season number - will be the directory created under the series name in the output directory
    output: str         # Output directory that contains your series directories

    def __init__(self, series_name, season, output_path):
        self.videos = {}
        self.series_name = series_name
        self.season = season
        self.output = output_path

    def retrieve_source_videos(self, source_path):
        source_videos = glob(f"{source_path}/*.mkv")
        source_videos.sort()
        self.videos = {k: "" for k in source_videos}

    def map_titles_to_videos(self, episode_titles, episode_start, extras_titles):
        dest = f"{self.output}/{self.series_name}/Season {self.season}"
        for i, k in enumerate(self.videos.keys()):
            ext = k.split(".")[-1]
            if i < len(episode_titles):
                ep_title = f"S{self.season:02d}E{i + episode_start:02d} {episode_titles[i]}.{ext}"
                self.videos[k] = f"{dest}/{validate_filename_characters(ep_title)}"
            else:
                ep_title = f"{extras_titles[i-len(episode_titles)]}.{ext}"
                self.videos[k] = f"{dest}/Extras/{validate_filename_characters(ep_title)}"

    def display(self):
        print("-" * 50)
        print("Series Name:", self.series_name)
        print("Season:", self.season)
        print("Input Directory:", os.path.dirname(list(self.videos.keys())[0]))
        print("Output Directory:", f"{self.output}/{self.series_name}/Season {self.season}\n")
        print("Episode Remapping")
        for k, v in self.videos.items():
            print(os.path.basename(k), "->", os.path.basename(v))
        print("-" * 50)
        print("")

    def transfer(self):
        dest = f"{self.output}/{self.series_name}/Season {self.season}/Extras"
        os.makedirs(dest, exist_ok=True)
        for k, v in self.videos.items():
            shutil.copy(k, v)

def parse_config(config_path):
    config = {}
    with open(config_path, "r", encoding="utf-8") as fp:
        config = json.load(fp)

    # TODO verification

    return config

def main():
    parser = ArgumentParser()

    parser.add_argument("-c", "--config", help="Path to JSON file containing configuration details")
    parser.add_argument("-e", "--example", help="Print example JSON file", action="store_true")

    args = parser.parse_args()

    if args.example:
        print_example_json()
        return

    if not args.config:
        print("Error! Configuration file not provided")
        parser.print_help()
        return

    if not os.path.exists(args.config):
        print("Error! Configuration file not found")
        parser.print_usage()
        return

    config =  parse_config(args.config)
    
    for c in config:
        series_section = SeriesSection(c["series_name"], c["season"], c["output"])
        series_section.retrieve_source_videos(c["source_videos"])
        series_section.map_titles_to_videos(c["episode_titles"], c.get("episode_start", 0) + 1, c["extra_titles"])
        series_section.display()
        response = input("Is this information correct? ")
        if response.lower() in ["y", "yes"]:
            print("Transfering files")
            series_section.transfer()
        else:
            print("Skipping Transfer - please update configuration file")

if __name__ == "__main__":
    main()
