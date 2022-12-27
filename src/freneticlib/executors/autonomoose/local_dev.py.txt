import os
import zipfile

import fabric

from .scenario_scaffolder import CopyScenarioScaffolder


def copy_scenario(scenario):
    """This is only for dev purposes, so Stefan can test on his linux laptop while developing on his main machine"""
    # use scaffolder to get required data
    scaff = CopyScenarioScaffolder(new_scenario_name=scenario)

    # read scenario map
    mapname = None
    with open(scaff.new_scenario_dir.absolute() / "scenario_config.bash", "r") as scenario_config:
        mapname = scenario_config.readlines()[1].split("maps/")[1].split("/")[0]

    # now copy to laptop
    # - scaff.new_scenario_dir
    # - os.path.join(scaff.maps_dir, mapname)
    # - scaff.new_simulation_configs_dir

    with fabric.Connection("lap") as conn:
        rsync_prefix = 'rsync -azv --exclude="*.DS_Store"'
        conn.local(f"{rsync_prefix} {scaff.new_scenario_dir} lap:~/wise-sim-scenarios/scenarios/ ")
        conn.local(f"{rsync_prefix} {os.path.join(scaff.maps_dir, mapname)} lap:~/wise-sim-scenarios/maps/ ")
        conn.local(f"{rsync_prefix} {scaff.new_simulation_configs_dir} lap:~/wise-sim-scenarios/simulation_configs/ ")


def run_scenario(scenario, restart_failed=1, rosbag_name=None):
    rosbag_option = "" if rosbag_name is None else f"-b $HOME/rosbags/{rosbag_name}"

    with fabric.Connection("lap") as conn:
        # run it!
        conn.run(
            """bash --login -i -c "export DISPLAY=:0 ; source ~/.bashrc ;"""
            + f"""python3 ~/WiseSimScripts/benchmarks/bench.py --restart-failed {restart_failed} """
            + f"""scenario {rosbag_option} {scenario}" """
        )


def fetch_rosbag(bagfile: str, local: str = None):
    with fabric.Connection("lap") as conn:
        conn.get(bagfile, local=local)


def create_scenario_zip(scenario):
    """packs the scenario, map and simulation config into a zip file!"""

    scaff = CopyScenarioScaffolder(new_scenario_name=scenario)

    # read scenario map
    mapname = None
    with open(scaff.new_scenario_dir.absolute() / "scenario_config.bash", "r") as scenario_config:
        mapname = scenario_config.readlines()[1].split("maps/")[1].split("/")[0]

    folders_to_zip = {
        "scenarios": scaff.new_scenario_dir,
        "maps": scaff.maps_dir / mapname,
        "simulation-configs": scaff.new_simulation_configs_dir,
    }

    with zipfile.ZipFile(scaff.wise_sim_dir / f"{scenario}.zip", "w", zipfile.ZIP_DEFLATED) as zip_file:
        for dirname, dir in folders_to_zip.items():
            for entry in dir.glob("*"):
                zip_file.write(entry, entry.relative_to(dir.parent.parent))
