#/usr/bin/env python3
import subprocess
import pickle
import argparse

def guess_generator():
    with open("eff_large.wordlist", "r") as wordlist:
        for line in wordlist:
            if line.startswith("c"):
                yield "{} horse battery staple".format(line.rstrip())


def check_guesses(volume_path, mount_path, status_file_path):
    status = {
        "success": set(),
        "failure": set(),
        "volume_path": volume_path,
    }
    try:
        with open(status_file_path, "rb") as status_file:
            status = pickle.load(status_file)

            if status["volume_path"] != volume_path:
                print("targeting volume '{}' but status file is for '{}'".format(volume_path, status["volume_path"]))
                exit(1)

            if status["success"]:
                print("successful passwords already known: {}".format(status["success"]))
                print("use a different status file to search again")
                return
    except FileNotFoundError:
        print("status file not found")

    for guess in guess_generator():
        if guess in status["failure"]:
            print("skipping '{}' - already attempted".format(guess))
            continue

        try:
            print("trying '{}'".format(guess))
            subprocess.check_call(["veracrypt", "--password={}".format(guess),
                                   "--protect-hidden=no", "--keyfiles=",
                                   # Prevents re-prompting for passphrase on failure.
                                   "--non-interactive",
                                   # 485 is the default for most devices.
                                   # "--pim=485",
                                   volume_path, mount_path],
                                   # Timeout allows faster guesses but may risk false negatives.
                                   # Added based on noticing that a failed password takes much longer than a successful one.
                                   # timeout=2
                                   )
            print("'{}' worked".format(guess))
            status["success"].add(guess)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            status["failure"].add(guess)

        with open(status_file_path, "wb") as status_file:
            pickle.dump(status, status_file)

        if status["success"]:
            return

    print("guesses exhausted")
    exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("volume_path")
    parser.add_argument("mount_path")
    parser.add_argument("status_file_path")
    args = parser.parse_args()
    check_guesses(args.volume_path, args.mount_path, args.status_file_path)

