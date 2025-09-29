import platform
import requests
import subprocess
from pathlib import Path

def get_platform_identifier():
    """Determines the platform identifier for chromedriver downloads."""
    system = platform.system()
    machine = platform.machine()
    if system == 'Linux' and machine == 'x86_64':
        return 'linux64'
    if system == 'Darwin':
        return 'mac-arm64' if machine == 'arm64' else 'mac-x64'
    if system == 'Windows':
        return 'win64' if platform.architecture()[0] == '64bit' else 'win32'
    return None

def get_chrome_version():
    """Detects the version of Google Chrome installed on the system."""
    try:
        result = subprocess.run(
            ['google-chrome', '--version'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip().split(' ')[2]
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

def get_driver_info():
    """
    Determines the correct chromedriver URL and expected path.
    """
    platform_id = get_platform_identifier()
    if not platform_id:
        raise RuntimeError(f"Unsupported platform: {platform.system()} {platform.machine()}")

    expected_driver_path = Path.cwd() / "chromedriver"
    if platform.system() == 'Windows':
        expected_driver_path = expected_driver_path.with_suffix('.exe')

    url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        browser_version = get_chrome_version()
        target_version_info = None

        if browser_version:
            major_version = browser_version.split('.')[0]
            for v_info in reversed(data['versions']):
                if v_info['version'].split('.')[0] == major_version:
                    target_version_info = v_info
                    break

        if not target_version_info:
            target_version_info = data['versions'][-1]
            print("Could not determine Chrome version. Using latest stable chromedriver.")

        for download in target_version_info['downloads']['chromedriver']:
            if download['platform'] == platform_id:
                return expected_driver_path, download['url']

        raise RuntimeError(f"Could not find a download URL for platform {platform_id}.")

    except requests.RequestException as e:
        raise RuntimeError(f"Error fetching chromedriver versions: {e}") from e