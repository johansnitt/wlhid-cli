# wlhid-cli

Polls battery, DPI and polling rate from a WLMouse device and outputs as JSON. Useful for status bar widgets and low battery notifications.

DPI and polling rate are read from whichever onboard profile is active.

## Supported Devices

Tested on the Ying Magnesium. Should also work with the Beast X 8K and other WLMouse devices on the standard 1K or 8K receivers. The non-8K Beast X is incompatible.

## Install

Requires Python 3.10+.

Install the `wlhid` command:

```sh
pipx install git+https://github.com/johansnitt/wlhid-cli
```

Or clone the repo:

```sh
git clone https://github.com/johansnitt/wlhid-cli
cd wlhid-cli
pip install -r requirements.txt
```

## Usage

```sh
# if installed using pipx
wlhid

# or from local directory
python wlhid_cli.py
```

- `-v` prints the raw request/reply frames to stderr.
- `--pid a874` filters by product ID, useful with multiple receivers plugged in.

| Device              | PID    |
| ------------------- | ------ |
| 1K Nano Receiver    | `a882` |
| Ying 8K Receiver    | `a874` |
| Ying (wired)        | `a875` |
| Beast X 8K Receiver | `a883` |
| Beast X 8K (wired)  | `a884` |

## Response

```json
{"battery_level": 67, "charging": false, "dpi": 800, "polling_rate": 1000}
```

`dpi` and `polling_rate` are `null` if they can't be read.

## Errors

On failure, stdout is `{"error": "<code>"}` and the details go to stderr.

| Code        | Cause                                                                                     |
| ----------- | ----------------------------------------------------------------------------------------- |
| `no_device` | No WLMouse device found, or none matching `--pid`                                         |
| `no_reply`  | Receiver found but the mouse did not respond, or returned an invalid response             |
| `io_error`  | Could not open or read the device, usually permissions (run with sudo or add a udev rule) |

## Adding fields

Find the request frame by watching [gm.wlmouse.gg](https://gm.wlmouse.gg/) traffic with DevTools and HIDDevice, then add its first 6 bytes to `HEADERS` in `wlmouse.py` and read it in `wlhid_cli.py`.

## Credits

Polling rate table and Beast X product IDs from [mee7ya/wlmouse-cli](https://github.com/mee7ya/wlmouse-cli).

## License

[GPL-3.0](LICENSE)
