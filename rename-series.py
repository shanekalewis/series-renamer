"""
Rename-Series

Tool to facillitate renaming episodes in series (ARM -> Jellyfin)
"""
from argparse import ArgumentParser
from glob import glob
import json
import os
import shutil

# CONFIG KEYS
KEY_SERIES = "series_name"
KEY_SEASON = "season"
KEY_EPISODE_START = "episode_start"
KEY_EPISODE_TITLES = "episode_titles"
KEY_EXTRAS_TITLES = "extra_titles"
KEY_SOURCE = "source_videos"
KEY_OUTPUT = "output"

CONFIG_REQUIRED_KEY_TYPES = {
    KEY_SERIES: str,
    KEY_SEASON: int,
    KEY_EPISODE_TITLES: list,
    KEY_SOURCE: str,
    KEY_OUTPUT: str,
}

CONFIG_OPTIONAL_KEY_TYPES = {
    KEY_EPISODE_START: int,
    KEY_EXTRAS_TITLES: list,
}

def print_example_json():
    example_config = [
        {
            KEY_SERIES: "Test Series",
            KEY_SEASON: 1,
            KEY_EPISODE_START: 5,
            KEY_EPISODE_TITLES: ["Title 1", "Title 2"],
            KEY_EXTRAS_TITLES: ["<title-for-extras>"],
            KEY_SOURCE: "<path-to-source-videos>",
            KEY_OUTPUT: "<path-to-video-library>" 
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
        if not os.path.exists(source_path):
            print(f"Error! Path '{source_path}' not found")
            return False
        source_videos = glob(f"{source_path}/*.mkv")
        source_videos.sort()
        self.videos = {k: "" for k in source_videos}
        if len(source_path) == 0:
            print(f"Warning: no videos (.mkv) found in '{source_path}'")
        return True

    def map_titles_to_videos(self, episode_titles, episode_start, extras_titles):
        dest = f"{self.output}/{self.series_name}/Season {self.season}"
        if len(self.videos) > len(episode_titles) + len(extras_titles):
            print(f"Error! Not enough titles provided for {self.series_name} - Season {self.season} - episode start {episode_start}")
            return False
        if len(self.videos) != len(episode_titles) + len(extras_titles):
            print("Warning: number of videos in directory does not match number of given titles.")
        
        for i, k in enumerate(self.videos.keys()):
            ext = k.split(".")[-1]
            if i < len(episode_titles):
                ep_title = f"S{self.season:02d}E{i + episode_start:02d} {episode_titles[i]}.{ext}"
                self.videos[k] = f"{dest}/{validate_filename_characters(ep_title)}"
            else:
                ep_title = f"{extras_titles[i-len(episode_titles)]}.{ext}"
                self.videos[k] = f"{dest}/Extras/{validate_filename_characters(ep_title)}"
        return True

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

def parse_config(config_path, break_on_error=False):
    config = {}
    error = False
    with open(config_path, "r", encoding="utf-8") as fp:
        config = json.load(fp)

    if isinstance(config, list):
        if error and break_on_error:
            return {}
        # Config version 1.0
        for idx,entry in enumerate(config):
            if error and break_on_error:
                break

            for k,t in CONFIG_REQUIRED_KEY_TYPES.items():
                if error and break_on_error:
                    break
                value = entry.get(k, None)
                if not value:
                    print(f"Error parsing entry {idx}! Required key '{k}' not found")
                    print(json.dumps(entry, indent=4))
                    error = True
                    continue
                if not isinstance(value, t):
                    print(f"Error parsing entry {idx}! Required key '{k}' expected type '{t}' but got type '{type(value)}'")
                    print(json.dumps(entry, indent=4))
                    error = True
                    continue
                if t == list and not all([isinstance(v, str) for v in value]):
                    print(f"Error parsing entry {idx}! Required key '{k}' expected a list of strings")
                    print(json.dumps(entry, indent=4))
                    error = True

            if error and break_on_error:
                return {}

            for k,t in CONFIG_OPTIONAL_KEY_TYPES.items():
                if error and break_on_error:
                    break
                value = entry.get(k, None)
                if not value:
                    continue
                if not isinstance(value, t):
                    print(f"Error parsing entry {idx}! Optional key '{k}' expected type '{t}' but got type '{type(value)}'")
                    print(json.dumps(entry, indent=4))
                    error = True
                    continue
                if t == list and not all([isinstance(v, str) for v in value]):
                    print(f"Error parsing entry {idx}! Optional key '{k}' expected a list of strings")
                    print(json.dumps(entry, indent=4))
                    error = True

    if error:
        return {}

    return config

def main():
    parser = ArgumentParser()

    parser.add_argument("-c", "--config", help="Path to JSON file containing configuration details")
    parser.add_argument("-e", "--example", help="Print example JSON file", action="store_true")
    parser.add_argument("-b", "--break-on-error", help="Break or end execution on error", action="store_true")

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

    config =  parse_config(args.config, args.break_on_error)
    if not config:
        print("Error parsing config!")
        return
    
    for c in config:
        series_section = SeriesSection(c["series_name"], c["season"], c["output"])
        ret = series_section.retrieve_source_videos(c["source_videos"])
        if not ret:
            if args.break_on_error:
                break
            continue
        ret = series_section.map_titles_to_videos(c["episode_titles"], c.get("episode_start", 0) + 1, c["extra_titles"])
        if not ret:
            if args.break_on_error:
                break
            continue
        series_section.display()
        response = input("Is this information correct? ")
        if response.lower() in ["y", "yes"]:
            print("Transfering files")
            series_section.transfer()
        else:
            print("Skipping Transfer - please update configuration file")

if __name__ == "__main__":
    main()
