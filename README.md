# espMountCtrl

Mount controller written in python for the [`esp-mount`](https://github.com/tomvitek/esp-mount) project. 

The project is in development stage, so lot of things might not work properly yet. To see usage examples, 
see `examples` directory. To run any of the samples, follow the installation instructions.

## Installation

Installation is really simple (assuming you have `python` and `pip` installed).

1) If you don't have `pipenv` installed, install it using `pip install pipenv` (use `pip3` instead of `pip` if you are still running python 2 as default)
2) Run `pipenv install` in the source root directory. Virtual environment will be initialised and all project's dependecies installed
3) Have fun :) You can to run some of the example scripts (for example, run `pipenv run python -m examples.mountSimple`)

## Connection to the mount
Mount uses UART (serial port) to communicate, so you will need a USB-to-UART converter with 3.3 V output (for example [this one](https://www.aliexpress.com/item/32665965133.html?spm=a2g0o.productlist.0.0.71a36c6dPXAVaP&algo_pvid=546efd86-0f94-4187-a2e3-024d9615e985&algo_exp_id=546efd86-0f94-4187-a2e3-024d9615e985-0&pdp_ext_f=%7B%22sku_id%22%3A%2212000025819932630%22%7D&pdp_npi=1%40dis%7CCZK%7C%7C39.11%7C%7C%7C19.67%7C%7C%402100bde316517835802947664e854d%7C12000025819932630%7Csea)).

Once you connect your computer to the mount controller, you should select the port it is connected to (e.g. `dev/ttyUSB0` on linux or `COM3` on windows).
You can either pass this directly to the `Mount.connect()` function (e.g. `mount.connect("COM3")`), or specify `ESP_MOUNT_PORT` environment variable.
When using vscode, you can add `.env` file to the root of your project with all required environment variables pre-initialized. 
The file than loads automatically each time you launch python.

Structure of the `.env` file is:
```sh
ESP_MOUNT_PORT=/dev/ttyUSB1
SOME_OTHER_VARIABLE=whatever_you_want_not_required    # You can also add comments
```