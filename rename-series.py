from argparse import ArgumentParser
from glob import glob
import json
import os

def print_example_json():
    example_config = [
        {
            "series_name": "Test Series",
            "season": 1,
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

class SeriesSection:
    videos: dict

    def __init__(self):
        self.videos = {}

    def retrieve_source_videos(self, source_path):
        source_videos = glob(f"{source_path}/*.mkv")
        source_videos.sort()
        self.videos = {k: "" for k in source_videos}

    def map_titles_to_videos(self, season, episode_titles, extras_titles):
        for i, k in enumerate(self.videos.keys()):
            if i < len(episode_titles):
                self.videos[k] = f"S{season:02d}E{i+1:02d} {episode_titles[i]}"
            else:
                self.videos[k] = f"{extras_titles[i-len(episode_titles)]}"

    def display(self, series_name, season, output):
        print("-" * 50)
        print("Series Name:", series_name)
        print("Season:", season)
        print("Output Directory:", f"{output}/{series_name}/Season {season}\n")
        print("Episode Remapping")
        for k, v in self.videos.items():
            print(os.path.basename(k), "->", v)
        print("-" * 50)
        print("")

def parse_config(config_path):
    config = {}
    with open(config_path, "r", encoding="utf-8") as fp:
        config = json.load(fp)

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
    
    series_sections = []

    for c in config:
        series_section = SeriesSection()
        series_section.retrieve_source_videos(c["source_videos"])
        series_section.map_titles_to_videos(c["season"], c["episode_titles"], c["extra_titles"])
        series_section.display(c["series_name"], c["season"], c["output"])
        series_sections.append(series_section)

if __name__ == "__main__":
    main()
